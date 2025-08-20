from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings

# Simple, typed agent you can extend
agent = Agent(
    'openai:gpt-4o',
    system_prompt="You are AgentFlow. Be concise, cite sources when available."
)
agent.settings = ModelSettings(temperature=0.1, max_tokens=500)

async def run_agent(prompt: str) -> str:
    result = await agent.run(prompt)
    return result.output_text
