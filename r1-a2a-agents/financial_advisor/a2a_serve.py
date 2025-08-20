from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.events import InMemoryQueueManager

from financial_advisor.executor import FinancialAgentExecutor
from financial_advisor.profile import financial_agent_card

    # Create request handler
request_handler = DefaultRequestHandler(
    agent_executor=FinancialAgentExecutor(),
    task_store=InMemoryTaskStore(),
    queue_manager=InMemoryQueueManager()
)

# Create A2A server with proper handler
financial_agent_app = A2AFastAPIApplication(
    agent_card=financial_agent_card,
    http_handler=request_handler
).build()
