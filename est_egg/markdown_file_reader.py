import os
import re
from typing import Dict, List, Optional

class MarkdownFileReader:
    """
    Utility class for reading and extracting requirements from markdown files.
    """
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        Read the content of a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Content of the file as a string
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    @staticmethod
    def extract_sections(content: str) -> Dict[str, str]:
        """
        Extract sections from markdown content based on headings.
        
        Args:
            content: Markdown content
            
        Returns:
            Dictionary with heading titles as keys and section content as values
        """
        sections = {}
        current_section = "main"
        section_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('#'):
                if section_content:  # Save previous section
                    sections[current_section] = '\n'.join(section_content).strip()
                    section_content = []
                
                # Extract new section title (remove # characters and trim)
                current_section = re.sub(r'^#+\s*', '', line).strip()
            else:
                section_content.append(line)
        
        # Save the last section
        if section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections
    
    @staticmethod
    def extract_requirements(content: str) -> List[str]:
        """
        Extract requirements from markdown content.
        Looks for sections marked as requirements and extracts their content.
        
        Args:
            content: Markdown content as string
            
        Returns:
            List of extracted requirements
        """
        # Simple extraction: consider all content as requirements
        # In a more advanced implementation, you could look for specific sections
        # marked with headers like "## Requirements" or bullet points
        
        # Split by headers to identify potential requirement sections
        sections = re.split(r'^#{1,6}\s+', content, flags=re.MULTILINE)
        
        # Filter out empty sections
        requirements = [section.strip() for section in sections if section.strip()]
        
        # If no clear sections, return the whole content
        if not requirements:
            requirements = [content]
            
        return requirements
