import logging

from fastapi import FastAPI, Request, HTTPException
from dapr.ext.fastapi import DaprApp, DaprActor

from dapr.actor import ActorProxy, ActorId

from actors.base_actor import BaseActor
from actors.interface import BaseActorInterface


# Set up logging
logging.basicConfig(level=logging.INFO)

# Create the Dapr gRPC app
app = FastAPI(title="PubSubActorService", description="Dapr Pub/Sub with Actors Example - Primary Lab")
dapr_app = DaprApp(app)
# Add Dapr Actor Extension
actor = DaprActor(app)

PUBSUB_NAME = "daca-pubsub" # Ensure this matches your pubsub.yaml component name
PUBSUB_TOPIC = "agent-stream-response" # Ensure this matches your subscription.yaml topic

# Register the actor
@app.on_event("startup")
async def startup():
    logging.info("Starting up the Ambient Agent")
    await actor.register_actor(BaseActor)
    logging.info(f"Registered actor: {BaseActor.__name__}")
    
# ✅ Programmatically subscribe to a topic
@dapr_app.subscribe(pubsub=PUBSUB_NAME, topic="agent-stream")
async def handle_order(request: Request):
    event = await request.json()
    logging.info(f"\n\n->[SUBSCRIPTION] Received Agent News: {event}\n\n")

    data = event.get("data", {})
    logging.info(f"\n\n->[SUBSCRIPTION] DATA: {data}\n\n")

    # Convert dict → Message
    user_message = "".join([part.get("text", "") for part in data.get("parts", []) if part.get("kind") == "text"])
    contextId = data.get("contextId", "")

    logging.info(f"Received user_message: {user_message}")
    logging.info(f"Received contextId: {contextId}")
    
    proxy = ActorProxy.create("BaseActor", ActorId(contextId), BaseActorInterface)
    input_data = {
        "new_message": user_message,
        "contextId": contextId
    }
    result = await proxy.ProcessMessage(input_data)
    
    print(f"Actor response: {result}")

    return {"status": "SUCCESS"}

@app.get("/actor/{actor_id}/history")
async def get_conversation_history(actor_id: str):
    """Get the conversation history."""
    try:
        proxy = ActorProxy.create("BaseActor", ActorId(actor_id), BaseActorInterface)
        history = await proxy.GetConversationHistory()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))