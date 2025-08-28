import os
import redis
import redis.asyncio as Redis

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.tasks import InMemoryTaskStore

from executor import FinancialAgentExecutor
from profile import financial_agent_card

from a2a_extensions.redis.redis_queue_manager import RedisQueueManager
from a2a_extensions.redis.redis_request_handler import create_redis_request_handler

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

queue_manager = RedisQueueManager(redis_client=redis_client, stream_prefix="a2a:task")
# Create request handler
request_handler = create_redis_request_handler(
    agent_executor=FinancialAgentExecutor(),
    task_store=InMemoryTaskStore(),
    redis_client=redis_client,
    stream_prefix="a2a:task",
)


# Create A2A server with proper handler
financial_agent_app = A2AFastAPIApplication(
    agent_card=financial_agent_card,
    http_handler=request_handler
).build()
