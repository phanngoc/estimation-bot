from typing import List, Dict, Optional, Any
from pydantic import Field
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema, BaseAgentOutputSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator
import instructor
import openai
import os
import re
from est_egg.markdown_file_reader import MarkdownFileReader

class SoftwareAnalysisInputSchema(BaseIOSchema):
    """
    Schema for the input to the software analysis agent.
    """
    requirement: Optional[str] = Field(default=None, description="Software requirement or feature description to analyze.")
    markdown_file_path: Optional[str] = Field(default=None, description="Path to a markdown file containing requirements.")

class TaskBreakdown(BaseIOSchema):
    """Schema for a single task in the breakdown."""
    task_id: str = Field(description="Unique identifier for the task")
    parent_id: Optional[str] = Field(default=None, description="Parent task ID if this is a subtask")
    task_name: str = Field(description="Name of the task")
    description: Optional[str] = Field(default=None, description="Detailed description of the task")
    difficulty: Optional[str] = Field(default=None, description="Difficulty level: Easy, Medium, Hard")
    time_estimate: Optional[str] = Field(default=None, description="Estimated time to complete (e.g., '2-4 hours', '1-2 days')")
    subtasks: List["TaskBreakdown"] = Field(default=[], description="Child tasks or subtasks")

class APIEndpoint(BaseIOSchema):
    """Schema for API endpoint analysis."""
    endpoint: Optional[str] = Field(default=None, description="API endpoint path")
    method: Optional[str] = Field(default=None, description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    purpose: Optional[str] = Field(default=None, description="Purpose of this endpoint")
    request_params: Optional[Dict[str, str]] = Field(default=None, description="Request parameters or body structure")
    response_structure: Optional[Dict[str, str]] = Field(default=None, description="Expected response structure")

class ERDEntity(BaseIOSchema):
    """Schema for ERD entity analysis."""
    entity_name: Optional[str] = Field(default=None, description="Name of the entity")
    attributes: Optional[Dict[str, str]] = Field(default=None, description="Attributes with their data types")
    relationships: Optional[List[str]] = Field(default=None, description="Relationships with other entities")

class DevelopmentComponent(BaseIOSchema):
    """Schema for a component in the development view."""
    component_name: str = Field(description="Name of the component")
    description: Optional[str] = Field(default=None, description="Description of what the component does")
    responsibilities: Optional[List[str]] = Field(default=None, description="Key responsibilities of this component")
    dependencies: Optional[List[str]] = Field(default=None, description="Components this one depends on")
    technologies: Optional[List[str]] = Field(default=None, description="Technologies or libraries used")
    
class ProcessFlow(BaseIOSchema):
    """Schema for a flow in the process view."""
    flow_name: str = Field(description="Name of the process flow")
    description: Optional[str] = Field(default=None, description="Description of what this flow does")
    actors: Optional[List[str]] = Field(default=None, description="Actors involved in this process")
    steps: Optional[List[str]] = Field(default=None, description="Steps in the process flow")

class SoftwareAnalysisOutputSchema(BaseIOSchema):
    """
    Schema for the output from the software analysis agent.
    """
    summary: Optional[str] = Field(default=None, description="Summary of the analysis for the requirement.")
    task_breakdown: Optional[List[TaskBreakdown]] = Field(default=[], description="Hierarchical breakdown of tasks needed to implement the requirement.")
    total_estimate: Optional[str] = Field(default=None, description="Total estimated time to complete all tasks.")
    api_analysis: List[APIEndpoint] = Field(default=[], description="Analysis of required API endpoints.")
    erd_analysis: List[ERDEntity] = Field(default=[], description="Analysis of required database entities and relationships.")
    development_view: List[DevelopmentComponent] = Field(default=[], description="Analysis of software components and packages.")
    process_view: List[ProcessFlow] = Field(default=[], description="Analysis of process flows (sequence and activity).")
    risks_and_considerations: Optional[List[str]] = Field(default=[], description="Potential risks and considerations for implementation.")
    suggested_questions: Optional[List[str]] = Field(default=[], description="Suggested follow-up questions for further analysis.")
    mermaid_task_diagram: Optional[str] = Field(default=None, description="Mermaid code for visualizing task hierarchy.")
    mermaid_erd_diagram: Optional[str] = Field(default=None, description="Mermaid code for visualizing entity relationships.")
    mermaid_component_diagram: Optional[str] = Field(default=None, description="Mermaid code for visualizing component relationships.")
    mermaid_sequence_diagram: Optional[str] = Field(default=None, description="Mermaid code for visualizing sequence flows.")

# Update circular reference for TaskBreakdown
TaskBreakdown.update_forward_refs()

# Set up the system prompt
system_prompt_generator = SystemPromptGenerator(
    background=[
        "You are an expert software analyst with deep knowledge of software development processes.",
        "You specialize in breaking down requirements, estimating development time, and analyzing architectural components.",
        "You understand APIs, databases, and modern software development practices.",
        "Your estimates are realistic and include buffer time for testing and edge cases.",
        "You can identify different types of entities in software systems like products, orders, users, categories, etc.",
        "You create hierarchical task breakdowns with clear parent-child relationships.",
        "You generate Mermaid diagrams to visualize task relationships and entity relationships.",
        "You can design development views showing components and packages of a system.",
        "You can design process views showing sequence and activity flows between components."
    ],
    steps=[
        "Analyze the requirement to understand the scope and complexity.",
        "Identify key software entities (like User, Product, Order, Category, etc.) in the requirements.",
        "Break down the requirement into specific implementable tasks with parent-child relationships.",
        "Estimate time for each task based on complexity and possible challenges.",
        "Design necessary API endpoints with detailed specifications.",
        "Identify database entities and their relationships needed for the feature.",
        "Identify components and packages needed for the implementation (development view).",
        "Design process flows showing how components interact in sequences and activities.",
        "Create Mermaid diagrams for task hierarchy and entity relationships.",
        "Create Mermaid diagrams for component relationships and sequence flows.",
        "Highlight potential risks and considerations.",
        "Suggest follow-up questions to clarify any ambiguities."
    ],
    output_instructions=[
        "Provide a concise summary of your understanding of the requirement.",
        "Break down tasks with realistic time estimates in a hierarchical structure.",
        "Be specific about API designs including endpoints, methods, and data structures.",
        "Include detailed ERD analysis with entities, attributes, and relationships.",
        "Include development view with components, their responsibilities and dependencies.",
        "Include process view with sequence or activity flows showing interactions.",
        "Generate Mermaid diagram code for the task hierarchy using flowchart syntax.",
        "Generate Mermaid diagram code for the entity relationships using ERD syntax.",
        "Generate Mermaid diagram code for component relationships using C4 or component diagram syntax.",
        "Generate Mermaid diagram code for sequence flows using sequence diagram syntax.",
        "Highlight any risks or special considerations for implementation.",
        "Suggest 3-5 relevant follow-up questions for further clarification."
    ]
)

class SoftwareAnalystAgent:
    """
    Agent for analyzing software requirements and generating estimations and diagrams.
    """
    
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("API key is required for SoftwareAnalystAgent")
        
        self.agent = BaseAgent(
            config=BaseAgentConfig(
                client=instructor.from_openai(openai.OpenAI(api_key=api_key)),
                model="gpt-4o",
                system_prompt_generator=system_prompt_generator,
                input_schema=SoftwareAnalysisInputSchema,
                output_schema=SoftwareAnalysisOutputSchema
            )
        )
    
    def analyze_from_text(self, requirement_text: str) -> SoftwareAnalysisOutputSchema:
        """
        Analyze requirements from direct text input.
        
        Args:
            requirement_text: The requirement text to analyze
            
        Returns:
            Analysis result with task breakdown and diagrams
        """
        input_data = SoftwareAnalysisInputSchema(requirement=requirement_text)
        result = self.agent.run(input_data)
        
        # Validate and fix common issues with Mermaid diagrams
        self._fix_mermaid_diagrams(result)
        
        return result
    
    def _fix_mermaid_diagrams(self, result: SoftwareAnalysisOutputSchema):
        """
        Fix common issues with Mermaid diagrams to ensure they render correctly.
        
        Args:
            result: The analysis result containing Mermaid diagrams
        """
        # Fix task diagram
        if result.mermaid_task_diagram:
            # Ensure proper graph definition at the start
            if not re.match(r'^(graph|flowchart)\s+[TBLR]D', result.mermaid_task_diagram):
                result.mermaid_task_diagram = "graph TD\n" + result.mermaid_task_diagram
            
        # Fix ERD diagram
        if result.mermaid_erd_diagram:
            # Ensure proper ERD definition
            if not re.match(r'^erDiagram', result.mermaid_erd_diagram):
                result.mermaid_erd_diagram = "erDiagram\n" + result.mermaid_erd_diagram
        
        # Fix component diagram
        if result.mermaid_component_diagram:
            # Check component diagram syntax
            if not any(re.match(r'^(graph|flowchart|classDiagram|C4Context)', result.mermaid_component_diagram)
                      for pattern in [r'^graph', r'^flowchart', r'^classDiagram', r'^C4Context']):
                result.mermaid_component_diagram = "flowchart TD\n" + result.mermaid_component_diagram
        
        # Fix sequence diagram
        if result.mermaid_sequence_diagram:
            # Check sequence diagram syntax
            if not re.match(r'^sequenceDiagram', result.mermaid_sequence_diagram):
                result.mermaid_sequence_diagram = "sequenceDiagram\n" + result.mermaid_sequence_diagram
    
    def analyze_from_markdown(self, file_path: str) -> SoftwareAnalysisOutputSchema:
        """
        Read requirements from a markdown file and analyze them.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Analysis result with task breakdown and diagrams
        """
        try:
            md_content = MarkdownFileReader.read_file(file_path)
            requirements = MarkdownFileReader.extract_requirements(md_content)
            
            # Combine all extracted requirements into a single text
            requirement_text = "\n\n".join(requirements)
            
            return self.analyze_from_text(requirement_text)
        except FileNotFoundError as e:
            print(f"Error: {str(e)}")
            return SoftwareAnalysisOutputSchema(
                summary=f"Failed to analyze: {str(e)}",
                task_breakdown=[],
                mermaid_task_diagram="",
                mermaid_erd_diagram=""
            )
    
    def analyze_from_multiple_markdown(self, file_paths: List[str]) -> SoftwareAnalysisOutputSchema:
        """
        Read requirements from multiple markdown files and analyze them together.
        
        Args:
            file_paths: List of paths to markdown files
            
        Returns:
            Analysis result with task breakdown and diagrams
        """
        try:
            all_requirements = []
            
            for file_path in file_paths:
                md_content = MarkdownFileReader.read_file(file_path)
                requirements = MarkdownFileReader.extract_requirements(md_content)
                file_name = os.path.basename(file_path)
                
                # Add header for each file's requirements
                file_requirements = [f"# From {file_name}:", ""] + requirements
                all_requirements.append("\n".join(file_requirements))
            
            # Combine all extracted requirements into a single text
            merged_requirements = "\n\n---\n\n".join(all_requirements)
            
            return self.analyze_from_text(merged_requirements)
        except Exception as e:
            print(f"Error processing markdown files: {str(e)}")
            return SoftwareAnalysisOutputSchema(
                summary=f"Failed to analyze: {str(e)}",
                task_breakdown=[],
                mermaid_task_diagram="",
                mermaid_erd_diagram=""
            )
    
    def print_analysis_results(self, response: SoftwareAnalysisOutputSchema):
        """
        Print the analysis results in a readable format.
        
        Args:
            response: The analysis response to print
        """
        print(f"\n{'=' * 80}")
        print(f"SOFTWARE REQUIREMENT ANALYSIS RESULTS")
        print(f"{'=' * 80}\n")
        
        print(f"SUMMARY:")
        print(f"{response.summary}\n")
        
        print(f"TASK BREAKDOWN:")
        self._print_task_hierarchy(response.task_breakdown)
        
        print(f"\nTOTAL ESTIMATE: {response.total_estimate}\n")
        
        print("API ANALYSIS:")
        for api in response.api_analysis:
            print(f"- {api.method} {api.endpoint}: {api.purpose}")
            print(f"  Request: {api.request_params}")
            print(f"  Response: {api.response_structure}\n")
        
        print("ENTITY RELATIONSHIP ANALYSIS:")
        for entity in response.erd_analysis:
            print(f"- Entity: {entity.entity_name}")
            print(f"  Attributes: {entity.attributes}")
            print(f"  Relationships: {entity.relationships}\n")
        
        print("DEVELOPMENT VIEW:")
        for component in response.development_view:
            print(f"- Component: {component.component_name}")
            print(f"  Description: {component.description}")
            print(f"  Responsibilities: {component.responsibilities}")
            print(f"  Dependencies: {component.dependencies}")
            print(f"  Technologies: {component.technologies}\n")
        
        print("PROCESS VIEW:")
        for flow in response.process_view:
            print(f"- Flow: {flow.flow_name}")
            print(f"  Description: {flow.description}")
            print(f"  Actors: {flow.actors}")
            print(f"  Steps: {flow.steps}\n")
        
        print("RISKS AND CONSIDERATIONS:")
        for risk in response.risks_and_considerations:
            print(f"- {risk}")
        
        print("\nSUGGESTED QUESTIONS:")
        for question in response.suggested_questions:
            print(f"- {question}")
        
        print("\nTASK HIERARCHY DIAGRAM (MERMAID CODE):")
        print(response.mermaid_task_diagram)
        
        print("\nENTITY RELATIONSHIP DIAGRAM (MERMAID CODE):")
        print(response.mermaid_erd_diagram)
        
        print("\nCOMPONENT DIAGRAM (MERMAID CODE):")
        print(response.mermaid_component_diagram)
        
        print("\nSEQUENCE DIAGRAM (MERMAID CODE):")
        print(response.mermaid_sequence_diagram)
    
    def _print_task_hierarchy(self, tasks, indent=0):
        """
        Recursively print the task hierarchy.
        
        Args:
            tasks: List of tasks to print
            indent: Current indentation level
        """
        for task in tasks:
            difficulty = f"({task.difficulty})" if task.difficulty else ""
            estimate = f"Est: {task.time_estimate}" if task.time_estimate else ""
            print(f"{'  ' * indent}- {task.task_name} {difficulty} {estimate}")
            if task.description:
                print(f"{'  ' * (indent+1)}Description: {task.description}")
            if task.subtasks:
                self._print_task_hierarchy(task.subtasks, indent + 1)


# Example usage
if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    analyst = SoftwareAnalystAgent(api_key)
    
    # Option 1: Analyze from direct text input
    requirement = "Implement a user authentication system with registration, login, password reset, and OAuth integration with Google and Facebook."
    result = analyst.analyze_from_text(requirement)
    analyst.print_analysis_results(result)
    
    # Option 2: Analyze from a markdown file
    # Uncomment to use
    # markdown_file = "/path/to/requirements.md"
    # result = analyst.analyze_from_markdown(markdown_file)
    # analyst.print_analysis_results(result)
