import logging

from fastapi import FastAPI, HTTPException
from dapr.ext.fastapi import DaprApp, DaprActor

from dapr.actor import ActorProxy, ActorId

from actors.base_actor import BaseActor
from actors.interface import BaseActorInterface

from pydantic import BaseModel

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
    
class AgentRequest(BaseModel):
    new_message: str
    contextId: str
    taskId: str

# ✅ Programmatically subscribe to a topic
@app.post("/agent-stream")
async def handle_order(request: AgentRequest):
    logging.info(f"\n\n->[SUBSCRIPTION] Received Agent News: {request}\n\n")
    
    proxy = ActorProxy.create("BaseActor", ActorId(request.contextId), BaseActorInterface)
    result = await proxy.ProcessMessage(request.model_dump())
    
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