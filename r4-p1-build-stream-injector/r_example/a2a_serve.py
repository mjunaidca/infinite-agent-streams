import os
import logging
from redis.asyncio import Redis
import redis
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.tasks import InMemoryTaskStore


from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from a2a.server.events.redis_queue_manager import RedisQueueManager
from a2a.server.request_handlers.redis_request_handler import create_redis_request_handler

from executor import FinancialAgentExecutor

logging.basicConfig(level=logging.DEBUG)

financial_agent_card = AgentCard(
    name="Financial Agent",
    description="Get latest financial advice",
    url="http://localhost:8003/",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="financial_advice",
            name="Financial Advice",
            description="Provide personalized financial advice",
            tags=["finance", "advice", "personalized"],
        ),
    ],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    preferred_transport="JSONRPC"
)


# Create agent executor
agent_executor = FinancialAgentExecutor()

REDIS_URL = os.getenv("REDIS_URL", "rediss://default:AYx3AAIncDEwZTBmZmQ0MWMyN2U0ZTBlOWM5NzVlZjQxMDNiNjk4ZnAxMzU5NTk@master-mayfly-35959.upstash.io:6379")
redis_client = Redis.from_url(REDIS_URL, 
                              decode_responses=True,  # Decode responses to strings
        max_connections=600,
        retry=redis.asyncio.retry.Retry(
            backoff=redis.backoff.ExponentialBackoff(),
            retries=5,  # Allow a reasonable number of retries before giving up
        ),
        retry_on_error=[
            redis.exceptions.ConnectionError,
            redis.exceptions.TimeoutError,
            redis.exceptions.ReadOnlyError,
            redis.exceptions.ClusterError,
        ],
)

# build a queue manager used by the server
queue_manager = RedisQueueManager(redis_client=redis_client, stream_prefix="a2a:task")
# Create request handler
request_handler = create_redis_request_handler(
    agent_executor=agent_executor,
    task_store=InMemoryTaskStore(),
    redis_client=redis_client,
    stream_prefix="a2a:task",
)

# Create A2A server
financial_agent_app = A2AFastAPIApplication(
    agent_card=financial_agent_card,
    http_handler=request_handler
).build()


def main():
    print("🔗 Agent Card: http://localhost:8003/.well-known/agent-card.json")
    print("📮 A2A Endpoint: http://localhost:8003")

    import uvicorn
    uvicorn.run(financial_agent_app, host="localhost", port=8003)
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
