from setuptools import setup, find_packages

setup(
    name="est_app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.8.0",
        "pandas>=1.3.0",
        "openai>=1.0.0",
        "instructor>=0.6.0",
        "streamlit-markdown>=1.1.0",  # Add this for Mermaid support
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Software Requirements Analyzer App",
)
