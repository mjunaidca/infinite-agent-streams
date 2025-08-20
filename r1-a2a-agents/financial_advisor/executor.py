from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.tasks import TaskUpdater
from a2a.server.events import EventQueue
from a2a.types import TextPart, TaskState, Part
from financial_advisor.agent_core import run_financial_advisor_agent

class FinancialAgentExecutor(AgentExecutor):
    """A2A executor that bridges A2A messages to OpenAI Agents SDK."""

    def __init__(self):
        self.context_id = None

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        print("context.context_id", context.context_id)
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        try:
            # Initialize task
            task = context.current_task
            if not task:
                await updater.submit()
            await updater.start_work()
            
            # Get user input from A2A context
            user_input = context.get_user_input()
            

            # Stream individual chunks
            async for delta_text in run_financial_advisor_agent(user_input):
                await updater.update_status(
                    state=TaskState.working,
                    message=updater.new_agent_message(
                        parts=[Part(root=TextPart(text=delta_text))]
                    ),
                    final=False
                )

            # Mark as completed
            await updater.complete()

        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                message=updater.new_agent_message(
                    parts=[Part(root=TextPart(text=f"❌ Currency agent failed: {str(e)}"))])
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """Cancel the current task."""
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.update_status(
            TaskState.failed,
            message=updater.new_agent_message([
                Part(root=TextPart(text="❌ Task cancelled"))
            ])
        )