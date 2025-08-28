"""This file implements the BaseActor for the DACA Actor Runtime."""
import logging
import json
from typing import cast
from datetime import datetime, UTC

from dapr.actor import Actor, ActorId
from dapr.aio.clients import DaprClient

from openai.types.responses import ResponseTextDeltaEvent

from agents import Runner, RunResultStreaming
from a2a.utils.message import new_agent_text_message
from a2a.types import TaskState

from actors.interface import BaseActorInterface
from agent_core import finance_advisor_agent

# Import our new StreamInjector for Redis streaming
from a2a_extensions.redis.stream_write.stream_injector import StreamInjector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PUBSUB_NAME = "daca-pubsub" # Ensure this matches your pubsub.yaml component name
PUBSUB_TOPIC = "agent-stream-response" # Ensure this matches your subscription.yaml topic
    
class BaseActor(Actor, BaseActorInterface):
    """
    Base class for DACA actors, providing stub implementations for the DACA BaseActorInterface.
    """

    def __init__(self, ctx, actor_id: ActorId):
        super().__init__(ctx, actor_id)
        self.actor_type = self.__class__.__name__
        logger.info(f"Actor '{self.id.id}' of type '{self.actor_type}' __init__ called.")

    async def _on_activate(self) -> None:
        logger.info(f"Actor '{self.id.id}' of type '{self.actor_type}' _on_activate: Activating.")

        status_exists = await self._state_manager.contains_state("actor_status")
        if not status_exists:
            initial_status = {
                "status": "active",
                "last_activated_at": datetime.now(UTC).isoformat(),
                "version": "1.0.0",  # Example version
            }
            await self._state_manager.set_state("actor_status", initial_status)
            logger.info(f"Actor '{self.id.id}': Initialized 'actor_status' state. Initial state: {initial_status}")
        else:
            # Optionally update activation time if status exists
            current_status = await self._get_actor_state("actor_status", default={})
            if isinstance(current_status, dict):  # Ensure it's a dictionary
                current_status["last_activated_at"] = datetime.now(UTC).isoformat()
                await self._state_manager.set_state("actor_status", current_status)
                logger.info(f"Actor '{self.id.id}': Updated 'last_activated_at' in 'actor_status'. Current state: {current_status}")
            else:
                logger.warning(f"Actor '{self.id.id}': 'actor_status' state exists but is not a dictionary. Re-initializing.")
                initial_status = {
                    "status": "active_reinitialized",
                    "last_activated_at": datetime.now(UTC).isoformat(),
                    "version": "1.0.0",  # Example version
                }
                await self._state_manager.set_state("actor_status", initial_status)

        # Further initialization, such as loading configuration or setting up default reminders/timers, would go here.
        logger.info(f"Actor '{self.id.id}' of type '{self.actor_type}' _on_activate: Activation complete.")

    async def _on_deactivate(self) -> None:
        logger.info(f"Actor '{self.id.id}' of type '{self.actor_type}' _on_deactivate: Deactivating.")

    # --- Interface Method Implementations (Stubs) ---
    async def process_message(
        self, input: dict[str, str | list | dict]
    ) -> dict[str, object] | None:
        logger.info(f"Actor '{self.id.id}' method 'process_message' called with: {input}")
        
        new_message = cast(str, input.get("new_message", None))
        contextId = cast(str, input.get("contextId", None))
        taskId = cast(str, input.get("taskId", None))
        
        # get conversation and context from state
        conversation = await self._get_actor_state("conversation")
        
        if conversation is None or not isinstance(conversation, list):
            conversation = []
            
        # add message to conversation
        conversation.append({"role": "user", "content": new_message})
        
        logger.info(f"\n\n Pre-engine Conversation: {conversation}\n\n")
        
        # Create StreamInjector for this task
        async with StreamInjector('rediss://default:AYx3AAIncDEwZTBmZmQ0MWMyN2U0ZTBlOWM5NzVlZjQxMDNiNjk4ZnAxMzU5NTk@master-mayfly-35959.upstash.io:6379') as injector:
            logger.info('StreamInjector connected for task streaming')

            # result = await engine.process_input(conversation, run_method=run_method)
            async with DaprClient(http_timeout_seconds=300) as d_client:
                logging.info(f"Starting financial advisor agent")

                stream_queue: RunResultStreaming = Runner.run_streamed(finance_advisor_agent, conversation)

                async for event in stream_queue.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        logging.info(f"Financial advisor agent response: {event.data.delta}")
                        # Also update status with message using the new update_status method
                        await injector.update_status(
                            context_id=contextId,
                            task_id=taskId,
                            status={'state': 'working'},
                            message=new_agent_text_message(context_id=contextId, task_id=taskId, text=event.data.delta)
                        )


                if stream_queue.final_output:
                    await injector.update_status(
                        context_id=contextId,
                        task_id=taskId,
                        status=TaskState.completed,
                        message=new_agent_text_message(context_id=contextId, task_id=taskId, text=""),
                        final=True
                    )
                    print(stream_queue.final_output)
                    print(stream_queue.to_input_list())

        # # We can get and save output if run_method is as run or run_sync
        await self._state_manager.set_state("conversation", stream_queue.to_input_list())
        return {
            "status": "received",
            "actor_id": self.id.id,
            "final_output": stream_queue.to_input_list()
        }

    async def get_conversation_history(self) -> list[dict]:
        """Retrieve conversation history."""
        try:
            history = await self._state_manager.get_state("conversation")
            return history if isinstance(history, list) else []
        except Exception as e:
            logging.error(f"Error getting history for {self._history_key}: {e}")
            return []

    # --- Internal Helper Methods ---
    # These methods are for internal use by the BaseActor and are not part of the
    # external BaseActorInterface. They are fundamental for the actor's operation.

    async def _get_actor_state(
        self, state_name: str, default: list[dict[str, str]] | None = []
    ) -> object | list[dict[str, str]] | None:
        """
        Helper to retrieve a specific state value.
        This is a thin wrapper around self._state_manager.get_state() primarily
        for centralized logging and default value handling.
        It could be replaced by direct calls if desired, sacrificing some logging clarity.
        """
        logger.debug(f"Actor '{self.id.id}': Attempting to get state '{state_name}'.")
        try:
            # Dapr's state_manager.get_state returns the value directly if found.
            # It raises a KeyError if not found.
            value = await self._state_manager.get_state(state_name)
            logger.debug(
                f"Actor '{self.id.id}': Retrieved state '{state_name}' successfully."
            )
            return value
        except (
            KeyError
        ):  # Dapr's actor._state_manager.get_state raises KeyError if key not found.
            logger.info(
                f"Actor '{self.id.id}': State '{state_name}' not found, returning default."
            )
            # add a new state with the default value
            await self._state_manager.set_state(state_name, default)
            return default
        except Exception as e:
            logger.error(
                f"Actor '{self.id.id}': Error getting state '{state_name}': {e}",
                exc_info=True,
            )
            return default