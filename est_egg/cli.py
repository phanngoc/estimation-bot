import argparse
import os
from est_egg.software_analyst_agent import SoftwareAnalystAgent

def main():
    """
    Command-line interface for the Software Analyst Agent.
    """
    parser = argparse.ArgumentParser(description="Software Requirement Analysis Tool")
    
    # Add OpenAI API key argument
    parser.add_argument("--api-key", help="OpenAI API key (overrides OPENAI_API_KEY environment variable)")
    
    # Create a subparser for the different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command for analyzing text input
    text_parser = subparsers.add_parser("analyze-text", help="Analyze requirements from text input")
    text_parser.add_argument("--text", required=True, help="Requirement text to analyze")
    
    # Command for analyzing markdown files
    md_parser = subparsers.add_parser("analyze-file", help="Analyze requirements from a markdown file")
    md_parser.add_argument("--file", required=True, help="Path to the markdown file containing requirements")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not provided")
        print("Please either:")
        print("  1. Set OPENAI_API_KEY environment variable")
        print("  2. Use --api-key argument")
        return
    
    # Initialize the agent
    try:
        analyst = SoftwareAnalystAgent(api_key)
        
        if args.command == "analyze-text":
            result = analyst.analyze_from_text(args.text)
            analyst.print_analysis_results(result)
        elif args.command == "analyze-file":
            result = analyst.analyze_from_markdown(args.file)
            analyst.print_analysis_results(result)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
