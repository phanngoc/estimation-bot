from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate

class ApiEstimate(BaseModel):
    method: str = Field(description="HTTP method")
    path: str = Field(description="API path")
    description: str = Field(description="API description")
    estimate: float = Field(description="Time estimate in mandays", default=0.0)  # Added default value

class AnalysisResult(BaseModel):
    apis: List[ApiEstimate] = Field(default_factory=list)  # Added default value
    total_estimate: float = Field(default=0.0)  # Added default value


def calculate_total_estimate(apis: List[ApiEstimate]) -> float:
    return sum(api.estimate for api in apis)

def format_output(analysis_result: AnalysisResult) -> str:
    output_lines = [
        f"- {api.method} {api.path} - {api.description} ({api.estimate} manday)"
        for api in analysis_result.apis
    ]
    
    output = "\n".join(output_lines)
    output += f"\n\nTổng lượng thời gian ước lượng: {analysis_result.total_estimate} (tính theo manday, 1 manday = 7hour)"
    
    return output

# Initialize language model with new pattern
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

def analyze_features(input_text: str) -> AnalysisResult:
    # Setup output parser
    parser = PydanticOutputParser(pydantic_object=AnalysisResult)
    
    # Load and format prompt
    with open("prompt.md", "r") as f:
        template = f.read()

    # Prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                template,
            ),
            ("human", "{query}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    # prompt = PromptTemplate(
    #     template=template,
    #     input_variables=["input"]
    # )
    print('input_text', input_text)
    # Generate analysis using new invoke pattern
    chain = prompt | llm | parser
    output = chain.invoke({"query": input_text})

    print('output:', output)
    # Calculate total
    total = calculate_total_estimate(output)
    print('total:', total)
    return AnalysisResult(apis=output, total_estimate=total)


# from typing import Union, Annotated, TypedDict, Optional

# # TypedDict
# class Joke(TypedDict):
#     """Joke to tell user."""

#     setup: Annotated[str, ..., "The setup of the joke"]
#     punchline: Annotated[str, ..., "The punchline of the joke"]
#     rating: Annotated[Optional[int], None, "How funny the joke is, from 1 to 10"]


# structured_llm = llm.with_structured_output(Joke)

# for chunk in structured_llm.stream("Tell me a joke about cats"):
#     print(chunk)

# system = """You are a hilarious comedian. Your specialty is knock-knock jokes. \
# Return a joke which has the setup (the response to "Who's there?") and the final punchline (the response to "<setup> who?").

# Here are some examples of jokes:

# example_user: Tell me a joke about planes
# example_assistant: {{"setup": "Why don't planes ever get tired?", "punchline": "Because they have rest wings!", "rating": 2}}

# example_user: Tell me another joke about planes
# example_assistant: {{"setup": "Cargo", "punchline": "Cargo 'vroom vroom', but planes go 'zoom zoom'!", "rating": 10}}

# example_user: Now about caterpillars
# example_assistant: {{"setup": "Caterpillar", "punchline": "Caterpillar really slow, but watch me turn into a butterfly and steal the show!", "rating": 5}}"""

# prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])

# few_shot_structured_llm = prompt | structured_llm
# few_shot_structured_llm.invoke("what's something funny about woodpeckers")