import streamlit as st
import os
import tempfile
import re
import shutil
from est_egg.software_analyst_agent import SoftwareAnalystAgent
import streamlit.components.v1 as components
import pandas as pd
import html
import uuid
from streamlit_markdown import st_markdown  # Import the streamlit-markdown package
from est_egg.database_manager import DatabaseManager
import json
import datetime

def display_task_hierarchy(tasks, level=0):
    """Render task breakdown as markdown with proper indentation"""
    result = ""
    for task in tasks:
        difficulty = f"({task.difficulty})" if task.difficulty else ""
        estimate = f"Est: {task.time_estimate}" if task.time_estimate else ""
        result += f"{'  ' * level}- **{task.task_name}** {difficulty} {estimate}\n"
        if task.description:
            result += f"{'  ' * (level+1)}{task.description}\n"
        if task.subtasks:
            result += display_task_hierarchy(task.subtasks, level + 1)
    return result

def convert_to_mandays(time_estimate_str):
    """Convert a time estimate string to mandays (1 manday = 7 hours)"""
    if not time_estimate_str:
        return ""
    
    # Check for hours
    hours_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours|hour|hrs|hr|h)', time_estimate_str, re.IGNORECASE)
    if hours_match:
        hours = float(hours_match.group(1))
        mandays = hours / 7
        return f"{mandays:.2f}"
    
    # Check for days
    days_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:days|day|d)', time_estimate_str, re.IGNORECASE)
    if days_match:
        days = float(days_match.group(1))
        return f"{days:.2f}"
    
    # If the format is not recognized, return the original
    return time_estimate_str

def build_task_table(tasks):
    """Build table data from task hierarchy"""
    task_rows = []
    
    def process_task(task, depth=0):
        # Convert time estimate to mandays if it exists
        estimate = task.time_estimate if task.time_estimate else ""
        manday_estimate = convert_to_mandays(estimate)
        
        # Add the task to the data with appropriate indentation
        row = {
            "Task Name": "• " * depth + task.task_name,
            "Difficulty": task.difficulty if task.difficulty else "",
            "Description": task.description if task.description else "",
            "Estimated Time (mandays)": manday_estimate,
            "Original Estimate": estimate
        }
        task_rows.append(row)
        
        # Process subtasks
        if task.subtasks:
            for subtask in task.subtasks:
                process_task(subtask, depth + 1)
    
    # Process all top-level tasks
    for task in tasks:
        process_task(task)
    
    return task_rows

def display_api_endpoints(apis):
    """Render API endpoints as markdown"""
    result = ""
    for api in apis:
        result += f"### {api.method} {api.endpoint}\n"
        if api.purpose:
            result += f"**Purpose**: {api.purpose}\n\n"
        
        if api.request_params:
            result += "**Request Parameters:**\n```json\n"
            result += str(api.request_params).replace("'", "\"") + "\n"
            result += "```\n\n"
        
        if api.response_structure:
            result += "**Response Structure:**\n```json\n"
            result += str(api.response_structure).replace("'", "\"") + "\n"
            result += "```\n\n"
    return result

def display_entities(entities):
    """Render entities as markdown"""
    result = ""
    for entity in entities:
        result += f"### {entity.entity_name}\n"
        
        if entity.attributes:
            result += "**Attributes:**\n```\n"
            for attr, type_info in entity.attributes.items():
                result += f"{attr}: {type_info}\n"
            result += "```\n\n"
        
        if entity.relationships:
            result += "**Relationships:**\n"
            for rel in entity.relationships:
                result += f"- {rel}\n"
            result += "\n"
    return result

def sanitize_mermaid(mermaid_code):
    """
    Sanitize mermaid code to avoid common syntax errors.
    
    Args:
        mermaid_code: Original mermaid code string
        
    Returns:
        Sanitized mermaid code
    """
    if not mermaid_code:
        return ""
        
    # Ensure there's proper spacing around the graph definition
    mermaid_code = re.sub(r'(graph\s+[TBLR]D)(\S)', r'\1 \2', mermaid_code)
    
    # Fix class definitions
    mermaid_code = re.sub(r'class\s+(\w+)\s+([^,;]+)([,;]?)', r'class \1 \2\3', mermaid_code)
    
    # Ensure there's proper line breaks between statements in different sections
    mermaid_code = re.sub(r'(\w+)(\s*[{])', r'\1 \2', mermaid_code)
    
    # Fix common ERD syntax issues
    mermaid_code = re.sub(r'(\w+)\s*{([^}]*)}', r'\1 {\2}', mermaid_code)
    
    # Fix sequence diagram participant definitions
    mermaid_code = re.sub(r'(participant|actor)\s+([^"]+)(?!")', r'\1 "\2"', mermaid_code)
    
    # Remove any unexpected characters
    mermaid_code = re.sub(r'[^\x00-\x7F]+', '', mermaid_code)
    
    return mermaid_code

def render_mermaid(mermaid_code, diagram_type=""):
    """
    Render Mermaid diagram using streamlit-markdown
    
    Args:
        mermaid_code: The mermaid diagram code to render
        diagram_type: Type of diagram for descriptive purposes
    """
    if not mermaid_code:
        st.info(f"No {diagram_type} diagram available.")
        return
        
    # Format the code as a mermaid code block for markdown rendering
    markdown_text = f"```mermaid\n{mermaid_code}\n```"
    
    try:
        # Render using st_markdown from streamlit-markdown package with a unique key
        diagram_id = f"mermaid-{uuid.uuid4().hex[:8]}"
        st_markdown(markdown_text, key=diagram_id)
        
        # Still display the code for reference
        with st.expander("View Mermaid Code"):
            st.code(mermaid_code, language="mermaid")
    except Exception as e:
        st.error(f"Error rendering diagram: {str(e)}")
        st.code(mermaid_code, language="mermaid")

def save_uploaded_file(uploaded_file, upload_dir):
    """
    Save an uploaded file to the specified directory
    
    Args:
        uploaded_file: The uploaded file object
        upload_dir: Directory to save the file in
        
    Returns:
        Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename to avoid overwriting
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    return file_path

def extract_requirement_from_file(uploaded_files):
    """Merge requirements from text input and uploaded files"""
    
    # Process uploaded files
    file_contents = []
    excel_files = []
    markdown_files = []
    
    for uploaded_file in uploaded_files:
        # Determine file type
        if uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
            excel_files.append(uploaded_file)
        else:
            # Assume it's markdown
            content = uploaded_file.read().decode("utf-8")
            file_contents.append(f"## From file: {uploaded_file.name}\n{content}")
            uploaded_file.seek(0)  # Reset file pointer after reading
            markdown_files.append(uploaded_file)
    
    # Return the merged requirements and separate Excel files
    return excel_files, markdown_files

def display_development_components(components):
    """Render development components as markdown"""
    result = ""
    for component in components:
        result += f"### {component.component_name}\n"
        
        if component.description:
            result += f"{component.description}\n\n"
        
        if component.responsibilities:
            result += "**Responsibilities:**\n"
            for resp in component.responsibilities:
                result += f"- {resp}\n"
            result += "\n"
        
        if component.dependencies:
            result += "**Dependencies:**\n"
            for dep in component.dependencies:
                result += f"- {dep}\n"
            result += "\n"
            
        if component.technologies:
            result += "**Technologies:**\n"
            for tech in component.technologies:
                result += f"- {tech}\n"
            result += "\n"
    return result

def display_process_flows(flows):
    """Render process flows as markdown"""
    result = ""
    for flow in flows:
        result += f"### {flow.flow_name}\n"
        
        if flow.description:
            result += f"{flow.description}\n\n"
        
        if flow.actors:
            result += "**Actors:**\n"
            for actor in flow.actors:
                result += f"- {actor}\n"
            result += "\n"
        
        if flow.steps:
            result += "**Process Steps:**\n"
            for i, step in enumerate(flow.steps, 1):
                result += f"{i}. {step}\n"
            result += "\n"
    return result

def render_diagrams(results):
    """Render all diagrams with proper handling for tab switching"""
    
    # Task Hierarchy Diagram
    st.subheader("Task Hierarchy Diagram")
    if results.mermaid_task_diagram:
        render_mermaid(results.mermaid_task_diagram, "task hierarchy")
    else:
        st.info("No task diagram available.")
        
    # Entity Relationship Diagram
    st.subheader("Entity Relationship Diagram")
    if results.mermaid_erd_diagram:
        render_mermaid(results.mermaid_erd_diagram, "entity relationship")
    else:
        st.info("No ERD diagram available.")
        
    # Component Diagram
    st.subheader("Component Diagram")
    if results.mermaid_component_diagram:
        render_mermaid(results.mermaid_component_diagram, "component")
    else:
        st.info("No component diagram available.")
        
    # Sequence Diagram
    st.subheader("Sequence Diagram")
    if results.mermaid_sequence_diagram:
        render_mermaid(results.mermaid_sequence_diagram, "sequence")
    else:
        st.info("No sequence diagram available.")

def load_query_from_db(query_id):
    """Load analysis results from database by query ID"""
    db = DatabaseManager()
    query = db.get_query_by_id(query_id)
    
    if not query:
        return False
    
    # Parse the result_data back into SoftwareAnalysisOutputSchema
    result_data = query["result_data"]
    
    # We need to reconstruct the full object structure from the serialized data
    from est_egg.software_analyst_agent import SoftwareAnalysisOutputSchema, TaskBreakdown, APIEndpoint, ERDEntity, DevelopmentComponent, ProcessFlow
    
    # Helper function to convert dictionaries back to their respective classes
    def dict_to_task_breakdown(task_dict):
        subtasks = []
        if "subtasks" in task_dict and task_dict["subtasks"]:
            subtasks = [dict_to_task_breakdown(subtask) for subtask in task_dict["subtasks"]]
        
        return TaskBreakdown(
            task_id=task_dict.get("task_id", ""),
            parent_id=task_dict.get("parent_id"),
            task_name=task_dict.get("task_name", ""),
            description=task_dict.get("description"),
            difficulty=task_dict.get("difficulty"),
            time_estimate=task_dict.get("time_estimate"),
            subtasks=subtasks
        )
    
    # Convert API endpoints
    api_endpoints = []
    if "api_analysis" in result_data:
        for api in result_data["api_analysis"]:
            api_endpoints.append(APIEndpoint(
                endpoint=api.get("endpoint"),
                method=api.get("method"),
                purpose=api.get("purpose"),
                request_params=api.get("request_params"),
                response_structure=api.get("response_structure")
            ))
    
    # Convert ERD entities
    erd_entities = []
    if "erd_analysis" in result_data:
        for entity in result_data["erd_analysis"]:
            erd_entities.append(ERDEntity(
                entity_name=entity.get("entity_name"),
                attributes=entity.get("attributes"),
                relationships=entity.get("relationships")
            ))
    
    # Convert development components
    dev_components = []
    if "development_view" in result_data:
        for comp in result_data["development_view"]:
            dev_components.append(DevelopmentComponent(
                component_name=comp.get("component_name", ""),
                description=comp.get("description"),
                responsibilities=comp.get("responsibilities"),
                dependencies=comp.get("dependencies"),
                technologies=comp.get("technologies")
            ))
    
    # Convert process flows
    proc_flows = []
    if "process_view" in result_data:
        for flow in result_data["process_view"]:
            proc_flows.append(ProcessFlow(
                flow_name=flow.get("flow_name", ""),
                description=flow.get("description"),
                actors=flow.get("actors"),
                steps=flow.get("steps")
            ))
    
    # Convert task breakdowns
    task_breakdowns = []
    if "task_breakdown" in result_data:
        for task in result_data["task_breakdown"]:
            task_breakdowns.append(dict_to_task_breakdown(task))
    
    # Create the output schema object
    output = SoftwareAnalysisOutputSchema(
        summary=result_data.get("summary"),
        task_breakdown=task_breakdowns,
        total_estimate=result_data.get("total_estimate"),
        api_analysis=api_endpoints,
        erd_analysis=erd_entities,
        development_view=dev_components,
        process_view=proc_flows,
        risks_and_considerations=result_data.get("risks_and_considerations", []),
        suggested_questions=result_data.get("suggested_questions", []),
        mermaid_task_diagram=result_data.get("mermaid_task_diagram"),
        mermaid_erd_diagram=result_data.get("mermaid_erd_diagram"),
        mermaid_component_diagram=result_data.get("mermaid_component_diagram"),
        mermaid_sequence_diagram=result_data.get("mermaid_sequence_diagram")
    )
    
    # Set the persist directory from the database
    st.session_state.persist_directory = query["persist_directory"]
    
    # Store the uploaded files info for display
    if "uploaded_files" in query and query["uploaded_files"]:
        st.session_state.uploaded_files = query["uploaded_files"]
    else:
        st.session_state.uploaded_files = []
    
    # Set the results in session state
    st.session_state.analysis_results = output
    
    return True

def main():
    st.set_page_config(
        page_title="Software Requirement Analyzer", 
        page_icon="📊", 
        layout="wide"
    )
    
    # Initialize the database manager
    db = DatabaseManager()
    
    st.title("Software Requirement Analyzer")
    st.markdown("Analyze software requirements to get task breakdowns, API designs, and entity-relationship diagrams.")
    
    # Initialize session states if needed
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("OPENAI_API_KEY", "")
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "diagrams_rendered" not in st.session_state:
        st.session_state.diagrams_rendered = False
    if "persist_directory" not in st.session_state:
        st.session_state.persist_directory = './data'
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    
    # Define uploads directory - relative to app directory
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    
    # Sidebar for input configuration
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", value=st.session_state.api_key, type="password")
    st.session_state.api_key = api_key
    
    # Add persistence directory setting
    persist_dir = st.sidebar.text_input("Database Directory", value=st.session_state.persist_directory)
    st.session_state.persist_directory = persist_dir
    
    # Display recent queries in the sidebar
    st.sidebar.header("Recent Analyses")
    recent_queries = db.get_recent_queries(limit=5)
    
    if recent_queries:
        for query in recent_queries:
            # Format timestamp for display
            timestamp = datetime.datetime.fromisoformat(query["timestamp"]).strftime("%Y-%m-%d %H:%M")
            
            # Create a descriptive label for the button
            label = f"{timestamp} - {query['result_summary'][:30]}..." if len(query['result_summary']) > 30 else query['result_summary']
            
            # Display uploaded files count if any
            if query.get("uploaded_files") and len(query["uploaded_files"]) > 0:
                label += f" ({len(query['uploaded_files'])} files)"
            
            if st.sidebar.button(label, key=f"query_{query['id']}"):
                if load_query_from_db(query["id"]):
                    st.success(f"Loaded analysis from {timestamp}")
                    st.rerun()
    else:
        st.sidebar.info("No previous analyses found")
    
    # Display uploaded files from previous analyses if loaded
    if st.session_state.uploaded_files:
        st.sidebar.subheader("Uploaded Files")
        for file_info in st.session_state.uploaded_files:
            filename = os.path.basename(file_info.get("path", ""))
            file_type = file_info.get("type", "Unknown")
            st.sidebar.text(f"📄 {filename} ({file_type})")
    
    # Replace radio buttons with checkboxes to allow multiple selections
    st.header("Requirement Input")
    col1, col2, col3 = st.columns(3)
    with col1:
        use_text_input = st.checkbox("Use Text Input", value=True)
    with col2:
        use_file_input = st.checkbox("Use Markdown Files", value=False)
    with col3:
        use_excel_input = st.checkbox("Use Excel Files", value=False)
    
    requirement_text = ""
    uploaded_files = []
    
    if use_text_input:
        requirement_text = st.text_area(
            "Enter your software requirement:",
            height=200,
            placeholder="Example: Implement a user authentication system with registration, login, password reset, and OAuth integration."
        )
    
    if use_file_input or use_excel_input:
        accepted_types = []
        if use_file_input:
            accepted_types.extend(["md"])
        if use_excel_input:
            accepted_types.extend(["xlsx", "xls"])
            
        uploaded_files = st.file_uploader(
            "Upload requirement files", 
            type=accepted_types, 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.subheader("File Previews")
            for i, uploaded_file in enumerate(uploaded_files):
                with st.expander(f"Preview: {uploaded_file.name}"):
                    if uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                        # For Excel files, display as dataframe
                        try:
                            df = pd.read_excel(uploaded_file)
                            uploaded_file.seek(0)  # Reset file pointer after reading
                            st.dataframe(df.head())
                        except Exception as e:
                            st.error(f"Error reading Excel file: {str(e)}")
                    else:
                        # For markdown files, show raw content
                        content = uploaded_file.read().decode("utf-8")
                        uploaded_file.seek(0)  # Reset file pointer after reading
                        st.text_area(f"File content:", value=content[:500] + ("..." if len(content) > 500 else ""), height=150, disabled=True)
    
    if st.button("Analyze Requirements"):
        # Check if any inputs are provided
        if not requirement_text.strip() and not uploaded_files:
            st.error("Please provide at least one input method (text, markdown or Excel files).")
            return
            
        if not api_key:
            st.error("Please provide your OpenAI API key.")
            return
            
        try:
            with st.spinner("Analyzing requirements..."):
                # Create analyst with persistence directory
                analyst = SoftwareAnalystAgent(
                    api_key=api_key,
                    persist_directory=st.session_state.persist_directory
                )
                
                # Save uploaded files to the uploads directory
                saved_files = []
                for uploaded_file in uploaded_files:
                    # Save the file
                    file_path = save_uploaded_file(uploaded_file, uploads_dir)
                    
                    # Determine file type
                    file_type = "Excel" if uploaded_file.name.lower().endswith(('.xlsx', '.xls')) else "Markdown"
                    
                    # Add to saved files list
                    saved_files.append({
                        "name": uploaded_file.name,
                        "path": file_path,
                        "type": file_type,
                        "size": os.path.getsize(file_path)
                    })
                    
                    # Reset file pointer for further processing
                    uploaded_file.seek(0)
                
                # Store saved files in session state
                st.session_state.uploaded_files = saved_files
                
                # Merge requirements from text and files
                excel_files, markdown_files = extract_requirement_from_file(uploaded_files)
                
                # Store file names for database
                file_names = [file.name for file in uploaded_files] if uploaded_files else []
                
                if markdown_files:
                    # Only Markdown files
                    for markdown_file in markdown_files:
                        analyst.index_from_markdown(markdown_file)
                # Analyze from Excel files if present
                if excel_files:
                    # Only Excel files
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_files = []
                        for excel_file in excel_files:
                            temp_path = os.path.join(temp_dir, excel_file.name)
                            with open(temp_path, "wb") as f:
                                f.write(excel_file.getbuffer())
                            temp_files.append(temp_path)
                        
                        # Use first Excel file for now
                        if temp_files:
                            analyst.index_from_excel(temp_files[0])
                            

                if requirement_text.strip():
                    print('Start update context search:')
                    analyst.get_context_provider().update_context(requirement_text)
                    results = analyst.analyze_from_text(requirement_text)
                
                # Save results to session state
                st.session_state.analysis_results = results
                
                # Save query and results to database
                db.save_query(
                    input_text=requirement_text,
                    input_files=file_names,
                    uploaded_files=saved_files,
                    persist_directory=st.session_state.persist_directory,
                    result_summary=results.summary,
                    result_data=results,
                    total_estimate=results.total_estimate or "Unknown"
                )
                
                st.success("Analysis complete and saved to history!")
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
    
    # Display uploaded files information
    if st.session_state.uploaded_files:
        st.header("Uploaded Files")
        files_df = pd.DataFrame([
            {
                "Filename": os.path.basename(file["path"]),
                "Type": file["type"],
                "Size (KB)": round(file["size"] / 1024, 2)
            }
            for file in st.session_state.uploaded_files
        ])
        st.dataframe(files_df, hide_index=True)
    
    # Display results if available
    if st.session_state.analysis_results:
        st.header("Analysis Results")
        results = st.session_state.analysis_results
        
        # Create tabs for different sections
        tabs = st.tabs([
            "Summary", 
            "Task Breakdown", 
            "API Endpoints", 
            "Entity Relationships",
            "Development View",
            "Process View", 
            "Risks & Questions",
            "Diagrams"
        ])
        
        # Tab 1: Summary
        with tabs[0]:
            st.subheader("Requirement Summary")
            st.markdown(results.summary)
            if results.total_estimate:
                st.info(f"**Total Estimated Time**: {results.total_estimate}")
        
        # Tab 2: Task Breakdown
        with tabs[1]:
            st.subheader("Task Breakdown")
            
            # Create a table for task breakdown
            task_data = build_task_table(results.task_breakdown)
            if task_data:
                df = pd.DataFrame(task_data)
                # Hide the original estimate column but keep it for reference
                columns_to_display = ["Task Name", "Difficulty", "Description", "Estimated Time (mandays)"]
                st.dataframe(
                    df[columns_to_display],
                    hide_index=True,
                    use_container_width=True
                )
                
                # Show the raw breakdown as well (optional - can be expanded)
                with st.expander("View Hierarchical Breakdown"):
                    task_md = display_task_hierarchy(results.task_breakdown)
                    st.markdown(task_md)
            else:
                st.info("No task breakdown available.")
        
        # Tab 3: API Endpoints
        with tabs[2]:
            st.subheader("API Endpoint Design")
            if results.api_analysis:
                api_md = display_api_endpoints(results.api_analysis)
                st.markdown(api_md)
            else:
                st.info("No API endpoints specified in the analysis.")
        
        # Tab 4: Entity Relationships
        with tabs[3]:
            st.subheader("Entity Relationship Analysis")
            if results.erd_analysis:
                erd_md = display_entities(results.erd_analysis)
                st.markdown(erd_md)
            else:
                st.info("No entities specified in the analysis.")
        
        # Tab 5: Development View
        with tabs[4]:
            st.subheader("Development View (Components & Packages)")
            if results.development_view:
                dev_md = display_development_components(results.development_view)
                st.markdown(dev_md)
            else:
                st.info("No development components specified in the analysis.")
        
        # Tab 6: Process View
        with tabs[5]:
            st.subheader("Process View (Sequences & Activities)")
            if results.process_view:
                process_md = display_process_flows(results.process_view)
                st.markdown(process_md)
            else:
                st.info("No process flows specified in the analysis.")
        
        # Tab 7: Risks & Questions
        with tabs[6]:
            st.subheader("Risks and Considerations")
            if results.risks_and_considerations:
                for risk in results.risks_and_considerations:
                    st.markdown(f"- {risk}")
            else:
                st.info("No risks identified.")
                
            st.subheader("Suggested Follow-up Questions")
            if results.suggested_questions:
                for question in results.suggested_questions:
                    st.markdown(f"- {question}")
            else:
                st.info("No follow-up questions suggested.")
        
        # Tab 8: Diagrams
        with tabs[7]:
            st.subheader("Diagram Rendering")
            # Add a button to explicitly render diagrams when the tab is selected
            if st.button("Render Diagrams", key="render_diagrams_button"):
                render_diagrams(results)

def run_streamlit():
    """Entry point for running the Streamlit app."""
    import sys
    import streamlit.web.bootstrap
    
    # Get the directory of the current file
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "streamlit_app.py")
    
    # Run the Streamlit app
    args = []
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    streamlit.web.bootstrap.run(filename, "", args, [])

if __name__ == "__main__":
    main()
