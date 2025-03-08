import os
import subprocess
import sys

def main():
    """Run the Streamlit app with the proper Python environment."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "streamlit_app.py")
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("Running Streamlit app...")
        cmd = [sys.executable, "-m", "streamlit", "run", app_path]
        subprocess.run(cmd)
    except ImportError:
        print("Streamlit is not installed. Please install it with:")
        print("pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()
