import json
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.tasks import TaskUpdater
from a2a.server.events import EventQueue
from a2a.types import TextPart, TaskState, Part

from dapr.aio.clients import DaprClient

PUBSUB_NAME = "daca-pubsub"
PUBSUB_TOPIC = "agent-stream"
AGENT_RESPONSE_TOPIC = "agent-stream-response"

# Use the queue protocol type rather than importing a concrete class
from a2a_extensions.redis.redis_event_consumer import QueueLike

class FinancialAgentExecutor(AgentExecutor):
    """A2A executor bridging messages to OpenAI Agents SDK with safe subscription handling."""
    
    async def execute(self, context: RequestContext, event_queue: QueueLike):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        try:
            if not context.current_task:
                await updater.submit()
            await updater.start_work()

            async with DaprClient(http_timeout_seconds=300) as d_client:
                # Publish the agent request
                await d_client.invoke_method(app_id="financial-advisor-agent",
                                             method_name="agent-stream",
                                             data=json.dumps({
                                                 "taskId": context.task_id,
                                                 "contextId": context.context_id,
                                                 "new_message": context.get_user_input()
                                                 }),
                                             http_verb="POST"
                                             )


        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                message=updater.new_agent_message(
                    [Part(root=TextPart(text=f"❌ Currency agent failed: {e}"))]
                ),
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """Signal cancellation to stop the execute loop safely."""
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.update_status(
            TaskState.failed,
            message=updater.new_agent_message(
                [Part(root=TextPart(text="❌ Task cancelled"))]
            ),
        )
