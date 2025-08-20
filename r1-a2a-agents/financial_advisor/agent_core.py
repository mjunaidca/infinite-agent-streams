import os

from dotenv import load_dotenv, find_dotenv
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner, RunResultStreaming
from openai.types.responses import ResponseTextDeltaEvent

from typing import AsyncGenerator

_: bool = load_dotenv(find_dotenv())

gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

# 1. Which LLM Service?
external_client: AsyncOpenAI = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 2. Which LLM Model?
llm_model: OpenAIChatCompletionsModel = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

# Create Agent
finance_advisor_agent: Agent = Agent(
    name="Currency Agent",
    instructions="""You are finance advisor assistant.""",
    model=llm_model,
)

async def run_financial_advisor_agent(input_text: str) -> AsyncGenerator[str, None]:
    """Run the financial advisor agent with the given input text.
    
    Args:
        input_text: The input text to process with the financial advisor agent.
        
    Yields:
        dict[str, Any]: Serializable dictionary representation of StreamEvent objects 
        containing agent responses, tool calls, handoffs, and other streaming events.
    """
    stream_queue: RunResultStreaming = Runner.run_streamed(finance_advisor_agent, input_text)
    
    async for event in stream_queue.stream_events():
        # Convert the StreamEvent to a serializable dictionary
        # This safely handles complex objects that can't be pickled
        try:
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield event.data.delta
        except Exception as e:
            # If serialization fails, yield an error event
            yield "Failed to serialize event"