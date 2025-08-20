from a2a.types import AgentCard, AgentCapabilities, AgentSkill

financial_agent_card = AgentCard(
    name="Financial Agent",
    description="Get latest financial advice",
    url="http://localhost:8001/",
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