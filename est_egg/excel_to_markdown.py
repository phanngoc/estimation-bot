import pandas as pd
import os
import uuid
from typing import List, Dict, Any, Tuple


class ExcelToMarkdown:
    """
    Converts Excel files to Markdown format for requirement analysis.
    """

    @staticmethod
    def convert_excel_to_markdown(file_path: str) -> str:
        """
        Convert an Excel file to Markdown format.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Markdown string representation of the Excel content
        """
        try:
            # Read all sheets from the Excel file
            excel = pd.ExcelFile(file_path)
            sheet_names = excel.sheet_names
            
            markdown_parts = []
            file_name = os.path.basename(file_path)
            markdown_parts.append(f"# Excel File: {file_name}\n")
            
            for sheet_name in sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Add sheet name as heading
                markdown_parts.append(f"## Sheet: {sheet_name}\n")
                
                # Convert to markdown table
                if not df.empty:
                    markdown_table = df.to_markdown(index=False)
                    markdown_parts.append(markdown_table)
                else:
                    markdown_parts.append("*Empty sheet*")
                
                markdown_parts.append("\n")
            
            return "\n".join(markdown_parts)
        except Exception as e:
            return f"# Error converting Excel file\n\nAn error occurred while converting the Excel file: {str(e)}"
    
    @staticmethod
    def convert_excel_bytes_to_markdown(file_content: bytes, file_name: str) -> str:
        """
        Convert Excel file content from bytes to Markdown format.
        
        Args:
            file_content: Bytes content of the Excel file
            file_name: Original filename for reference
            
        Returns:
            Markdown string representation of the Excel content
        """
        try:
            # Create a temporary file
            temp_file_path = f"/tmp/{uuid.uuid4()}_{file_name}"
            
            # Write bytes to temporary file
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            # Convert using the file-based method
            markdown = ExcelToMarkdown.convert_excel_to_markdown(temp_file_path)
            
            # Clean up
            os.remove(temp_file_path)
            
            return markdown
        except Exception as e:
            return f"# Error converting Excel file\n\nAn error occurred while converting the Excel file: {str(e)}"
    
    @staticmethod
    def extract_requirements_from_markdown(markdown: str) -> List[str]:
        """
        Extract potential requirements from a markdown string.
        
        Args:
            markdown: The markdown content to analyze
            
        Returns:
            List of requirement statements extracted from markdown
        """
        requirements = []
        
        # Split by headers to identify sections
        sections = markdown.split('#')
        
        for section in sections:
            if section.strip():
                # Look for table rows as potential requirements
                lines = section.split('\n')
                for line in lines:
                    # Ignore table headers and separators
                    if '|' in line and not line.strip().startswith('|:') and not line.strip().startswith('|-'):
                        # Extract text from table cells that might be requirements
                        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                        for cell in cells:
                            # Heuristic: Requirements often contain verbs like "implement", "create", "add", etc.
                            requirement_keywords = ["implement", "create", "add", "develop", "build", "support", 
                                                   "enable", "allow", "provide", "include", "design", "should", 
                                                   "must", "will", "shall", "needs to", "required"]
                            
                            if any(keyword in cell.lower() for keyword in requirement_keywords) and len(cell) > 20:
                                requirements.append(cell)
        
        return requirements
