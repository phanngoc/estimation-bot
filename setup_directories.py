import os
import sys

def setup_project_directories():
    """
    Set up the project directory structure.
    """
    # Get the project root directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define required directories
    directories = [
        os.path.join(project_dir, "uploads"),
        os.path.join(project_dir, "data"),
    ]
    
    # Create directories if they don't exist
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {str(e)}")
        else:
            print(f"Directory already exists: {directory}")

if __name__ == "__main__":
    setup_project_directories()
