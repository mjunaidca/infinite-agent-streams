import logging
import json

from fastapi import FastAPI, Request
from dapr.ext.fastapi import DaprApp
from dapr.aio.clients import DaprClient

from agent_core import run_financial_advisor_agent

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create the Dapr gRPC app
app = FastAPI(title="PubSubActorService", description="Dapr Pub/Sub with Actors Example - Primary Lab")
dapr_app = DaprApp(app)

PUBSUB_NAME = "daca-pubsub" # Ensure this matches your pubsub.yaml component name
PUBSUB_TOPIC = "agent-stream-response" # Ensure this matches your subscription.yaml topic
    
# ✅ Programmatically subscribe to a topic
@dapr_app.subscribe(pubsub=PUBSUB_NAME, topic="agent-stream")
async def handle_order(request: Request):
    event = await request.json()
    logging.info(f"\n\n->[SUBSCRIPTION] Received Agent News: {event}\n\n")

    data = event.get("data", {})
    logging.info(f"\n\n->[SUBSCRIPTION] DATA: {data}\n\n")

    # Convert dict → Message
    user_message = "".join([part.get("text", "") for part in data.get("parts", []) if part.get("kind") == "text"])

    logging.info(f"Received user_message: {user_message}")
    
    topic = f"""{PUBSUB_TOPIC}-{data.get("contextId")}"""
    print("RESPONSR TOPIC", topic)

    async with DaprClient(http_timeout_seconds=300) as d_client:
        logging.info(f"Starting financial advisor agent with message: {user_message}")

        # ✅ Stream agent deltas
        async for delta_text in run_financial_advisor_agent(user_message):
            resp = {
                "text": delta_text,
                "contextId": data.get("contextId"),  # 👈 keep camelCase
                "taskId": data.get("taskId"),
            }
            logging.info(f"\nPublishing chunk: {resp}\n")
            await d_client.publish_event(
                pubsub_name=PUBSUB_NAME,
                topic_name=topic,
                data=json.dumps(resp).encode("utf-8"),
                data_content_type="application/json",
            )

        # ✅ Final done event
        done_event = {
            "done": True,
            "contextId": data.get("contextId"),
            "taskId": data.get("taskId"),
        }
        logging.info(f"\nPublishing DONE: {done_event}\n")
        await d_client.publish_event(
            pubsub_name=PUBSUB_NAME,
            topic_name=topic,
            data=json.dumps(done_event).encode("utf-8"),
            data_content_type="application/json",
        )

    return {"status": "SUCCESS"}