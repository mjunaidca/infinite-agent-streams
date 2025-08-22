from fastapi import FastAPI
from a2a_serve import financial_agent_app

app = FastAPI()

app.mount("/", financial_agent_app)

def main():
    print("🔗 Agent Card: http://localhost:8001/.well-known/agent-card.json")
    print("📮 A2A Endpoint: http://localhost:8001/a2a")

    import uvicorn
    uvicorn.run(app, host="localhost", port=8001)
    

if __name__ == "__main__":
    main()