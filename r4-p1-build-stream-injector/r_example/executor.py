import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.tasks import TaskUpdater
from a2a.types import TextPart, TaskState, Part
from a2a.utils.message import new_agent_text_message
from a2a.server.events import EventQueue

# Use the queue protocol type rather than importing a concrete class
from a2a.server.events.redis_event_consumer import QueueLike

# Import our new StreamInjector for Redis streaming
from a2a.utils.stream_write.stream_injector import StreamInjector



logger = logging.getLogger(__name__)

mock_responses = [
    "Sure, I can help with that.",
    "The current exchange rate for", 
    "USD to EUR is approximately 0.85.",
    "Would you like to know about", 
    "historical trends as well?",
    "Let me fetch the latest data", 
    "for you.",
    "Here are some investment", 
    "options", 
    "based on your profile.",
    "Bye"
]

async def run_financial_advisor_agent(user_input: str, context_id: str, task_id: str, injector: StreamInjector):
    """Generator that yields financial advisor responses with StreamInjector events."""
    # Validate inputs
    if not context_id:
        raise ValueError('context_id cannot be empty')
    if not task_id:
        raise ValueError('task_id cannot be empty')

    logger.info('StreamInjector connected for task streaming')

    # Stream each response as both a yielded value AND a Redis event
    for i, response in enumerate(mock_responses):
        # Yield the response for the caller
        yield response

        # Also update status with message using the new update_status method
        await injector.update_status(
            context_id=context_id,
            task_id=task_id,
            status={'state': 'working'},
            message=new_agent_text_message(context_id=context_id, task_id=task_id, text=response)
        )


class FinancialAgentExecutor(AgentExecutor):
    """A2A executor that bridges A2A messages to OpenAI Agents SDK with Redis Streaming."""

    def __init__(self):
        self.context_id = None
        logger.info('FinancialAgentExecutor initialized')

    async def execute(self, context: RequestContext, event_queue: QueueLike) -> None:
        """Execute the financial advisor agent with Redis streaming."""
        logger.info('FinancialAgentExecutor.execute called with task_id: %s', context.task_id)
        print('context.context_id', context.context_id)
        
        # Create StreamInjector for Redis streaming
        injector = StreamInjector('rediss://default:AYx3AAIncDEwZTBmZmQ0MWMyN2U0ZTBlOWM5NzVlZjQxMDNiNjk4ZnAxMzU5NTk@master-mayfly-35959.upstash.io:6379')
        await injector.connect()
        
        # Create updater for framework compatibility (handle type issues)
        updater = None
        try:
            # Try to create TaskUpdater with proper type handling
            updater = TaskUpdater(event_queue, context.task_id or '', context.context_id or '')  # type: ignore

            # Initialize task
            task = context.current_task
            if not task:
                await updater.submit()
            await updater.start_work()
            
            # Get user input from A2A context
            user_input = context.get_user_input()

            # Stream individual chunks
            chunk_count = 0
            async for delta_text in run_financial_advisor_agent(user_input, context_id=context.context_id or '', task_id=context.task_id or '', injector=injector):
                chunk_count += 1
                logger.info('Processing chunk', extra={'chunk_count': chunk_count, 'text_preview': delta_text[:50]})
                
                # The RedisEventQueue will automatically handle Redis streaming
                # Also send to local queue for framework compatibility
                await updater.update_status(
                    state=TaskState.working,
                    message=updater.new_agent_message(
                        parts=[Part(root=TextPart(text=delta_text))]
                    ),
                    final=False
                )

            logger.info('Total chunks processed', extra={'chunk_count': chunk_count})
            
            # Mark as completed - RedisEventQueue will handle Redis streaming
            await updater.complete()
            logger.info('Marked task as completed')

        except Exception as e:
            logger.exception('Agent execution failed', extra={'error': str(e)})
            # Send error to queue if updater was created
            if updater:
                await updater.update_status(
                    TaskState.failed,
                    message=updater.new_agent_message(
                        parts=[Part(root=TextPart(text=f'❌ Currency agent failed: {e!s}'))])
                )
        finally:
            # Always disconnect from Redis
            await injector.disconnect()

    async def cancel(self, context: RequestContext, event_queue: QueueLike) -> None:
        """Cancel the current task."""
        logger.info('FinancialAgentExecutor.cancel called', extra={'task_id': context.task_id})

        updater = TaskUpdater(event_queue, context.task_id or '', context.context_id or '')  # type: ignore
        await updater.update_status(
            TaskState.failed,
            message=updater.new_agent_message([
                Part(root=TextPart(text='❌ Task cancelled'))
            ])
        )
