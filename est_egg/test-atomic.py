from typing import List
from pydantic import Field
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema, BaseAgentOutputSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator
import instructor
import openai
import os

class CustomInputSchema(BaseIOSchema):
    """
    Schema for the input to the agent.
    """
    user_input: str = Field(..., description="User's input to the agent.")

class CustomOutputSchema(BaseIOSchema):
    """
    Schema for the output from the agent.
    """
    chat_message: str = Field(..., description="The agent's response message.")
    suggested_questions: List[str] = Field(..., description="Suggested follow-up questions.")

# Set up the system prompt
system_prompt_generator = SystemPromptGenerator(
    background=[
        "You are a knowledgeable assistant that provides helpful information and suggests follow-up questions."
    ],
    steps=[
        "Analyze the user's input to understand the context and intent.",
        "Provide a relevant and informative response.",
        "Generate 3 suggested follow-up questions."
    ],
    output_instructions=[
        "Ensure clarity and conciseness in your response.",
        "Conclude with 3 relevant suggested questions."
    ]
)
api_key = os.environ.get("OPENAI_API_KEY")
print('api_key', api_key)
# Initialize the agent
agent = BaseAgent(
    config=BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=api_key)),
        model="gpt-4o",
        system_prompt_generator=system_prompt_generator,
        input_schema=CustomInputSchema,
        output_schema=CustomOutputSchema
    )
)

user_input = "Estimate the time needed to implement a feature that allows users to upload images to the system."
user_input = CustomInputSchema(user_input=user_input)

# Use the agent
response = agent.run(user_input)
print(f"Agent: {response.chat_message}")
print("Suggested questions:")
for question in response.suggested_questions:
    print(f"- {question}")