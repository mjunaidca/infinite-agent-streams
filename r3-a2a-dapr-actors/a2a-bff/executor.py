import asyncio
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.tasks import TaskUpdater
from a2a.server.events import EventQueue
from a2a.types import TextPart, TaskState, Part

from dapr.aio.clients import DaprClient

PUBSUB_NAME = "daca-pubsub"
PUBSUB_TOPIC = "agent-stream"
AGENT_RESPONSE_TOPIC = "agent-stream-response"


class FinancialAgentExecutor(AgentExecutor):
    """A2A executor bridging messages to OpenAI Agents SDK with safe subscription handling."""
    
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        try:
            if not context.current_task:
                await updater.submit()
            await updater.start_work()

            async with DaprClient(http_timeout_seconds=300) as d_client:
                # Subscribe to agent response topic
                
                # Publish the agent request
                await d_client.publish_event(
                    pubsub_name=PUBSUB_NAME,
                    topic_name=PUBSUB_TOPIC,
                    data=context.message.model_dump_json() if context.message else b"{}",
                    data_content_type="application/json",
                )

                response_stream = await d_client.subscribe(PUBSUB_NAME, AGENT_RESPONSE_TOPIC)
                try:
                    async for message in response_stream:

                        data = message.data()
                        msg_context_id = data.get("contextId") or data.get("context_id")

                        if msg_context_id != context.context_id:
                            # Skip messages not meant for this context
                            continue

                        chunk = data.get("assistant_chunk")
                        if chunk:
                            await updater.update_status(
                                state=TaskState.working,
                                message=updater.new_agent_message(
                                    parts=[Part(root=TextPart(text=chunk))]
                                ),
                                final=False
                            )

                        if data.get("isFinal") is True:
                            await updater.update_status(
                                TaskState.completed,
                                message=updater.new_agent_message(
                                    parts=[Part(root=TextPart(text="✅ Agent completed successfully."))]
                                )
                            )
                            break
                except Exception as e:
                    await updater.update_status(
                        TaskState.failed,
                        message=updater.new_agent_message(
                            [Part(root=TextPart(text=f"❌ Agent execution failed: {e}"))]
                        )
                    )
                finally:
                    await response_stream.close()

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
