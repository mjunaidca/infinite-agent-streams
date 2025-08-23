"""This file defines the external contract for the DACA Base Actor Runtime."""

from dapr.actor import ActorInterface, actormethod

class BaseActorInterface(ActorInterface):
    """
    Defines the comprehensive external contract for the DACA Base Actor Runtime.

    The docstrings provide details on arguments, return values, and the purpose ("What, Why, How")
    of each method, including considerations for future milestones like M6 background handoffs.
    """

    # --- Core Interaction & Event Handling ---
    @actormethod(name="ProcessMessage")
    async def process_message(
        self, input: dict[str, str | list | dict]
    ) -> dict[str, object] | None:
        """
        What:
            Handles generic synchronous messages, commands, or queries sent to the actor.
            This is a versatile entry point for various synchronous interactions.
        Why:
            Fulfills the 'Reactive & Real-Time Processing' promise by enabling low-latency,
            versatile message handling. The actor can signal an outgoing stream via the response.
        How:
            The actor's internal logic processes the `message_data` (which should specify
            the intended action or query) in real-time, potentially updating state,
            triggering events, or initiating workflows. Supports 'Flexible Agent Engine
            Integration' by handling diverse payloads. In M6, may initiate background handoffs.
            Aligns with 12-Factor Agents (Factor 6: Expose control via APIs).

        Args:
            input (dict[str, str | list | dict]): A dictionary containing all necessary data for processing.
                Expected keys typically include:
                - "message_data": dict, the actual message from the user (e.g., {"role": "user", "content": "Hi"}).
                - "engine_config": dict, configuration for the agentic engine (e.g., {"run_method": "run", "model": "..."}).
                - "engine_type": str, specifying the type of engine (e.g., "openai").

        Returns:
            dict[str, object] | None: A dictionary containing the processing status and result.
                Example Success: `{"status": "success", "result": {"answer": "AI is..."}}`
                Example Streaming: `{"status": "accepted_for_streaming", "stream_id": "unique_session_id", "stream_info": {"output_topic": "actor_stream_topic"}}`
                Example Error: `{"status": "error", "error_message": "Failed to process."}`
                Returns `None` if the interface method is not implemented.
        """
        pass

    @actormethod(name="GetConversationHistory")
    async def get_conversation_history(self) -> list[dict] | None:
        """Retrieve conversation history."""
        pass

