from typing import Dict, Any, List, Optional
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase
from est_egg.chroma_db_manager import ChromaDBManager


class RequirementContextProvider(SystemPromptContextProviderBase):
    """
    Context provider that enhances the system prompt with relevant requirements from ChromaDB.
    """
    
    def __init__(self, title: str, chroma_db_manager: ChromaDBManager, max_results: int = 5):
        """
        Initialize the requirement context provider.
        
        Args:
            title: Title of the context provider
            chroma_db_manager: ChromaDBManager instance for querying requirements
            max_results: Maximum number of relevant requirements to include
        """
        super().__init__(title=title)
        self.chroma_db = chroma_db_manager
        self.max_results = max_results
        self.context_parts = ""

    def update_context(self, query: str) -> Dict[str, Any]:
        """
        Update the context with the requirement query.
        
        Args:
            query: Requirement query
        
        Returns:
            Updated context
        """
            
        # Get similar requirements from ChromaDB
        similar_requirements = self.chroma_db.query_similar_requirements(
            query=query,
            n_results=self.max_results
        )
        
        # Log the retrieved similar requirements
        print(f"Retrieved {len(similar_requirements)} similar requirements")
        for i, req in enumerate(similar_requirements):
            print(f"Requirement {i+1}: {req.get('content', '')[:50]}... | Score: {req.get('relevance_score', 'N/A')}")

        if not similar_requirements:
            return "No similar historical requirements found in the database."
        
        # Format the context
        context_parts = ["### Similar Historical Requirements", ""]
        
        for i, req in enumerate(similar_requirements, 1):
            source = req["metadata"].get("source", "Unknown source")
            relevance = req["relevance_score"]
            context_parts.append(f"**Requirement {i}** (Source: {source}, Relevance: {relevance:.2f})")
            context_parts.append(f"{req['content']}")
            context_parts.append("")
        
        self.context_parts = "\n".join(context_parts)
        return self.context_parts

    def get_info(self) -> str:
        """
        Get context from ChromaDB based on the current input.
        
        Args:
            current_input: Current input to the agent
            
        Returns:
            Context as string to inject into the system prompt
        """
        print('get_info', self.context_parts)
        return self.context_parts


class RequirementContextManager:
    """
    Manager class for initializing and configuring the requirement context provider.
    """
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the requirement context manager.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.chroma_db = ChromaDBManager(persist_directory)
        self.context_provider = RequirementContextProvider("spec_file", self.chroma_db)
    
    def add_requirement(self, content: str, source: str) -> str:
        """
        Add a requirement to ChromaDB.
        
        Args:
            content: Requirement content
            source: Source of the requirement
            
        Returns:
            ID of the stored document
        """
        return self.chroma_db.add_requirement(content, source)
    
    def add_multiple_requirements(self, contents: List[str], source: str) -> List[str]:
        """
        Add multiple requirements to ChromaDB.
        
        Args:
            contents: List of requirement contents
            source: Source of the requirements
            
        Returns:
            List of IDs for the stored documents
        """
        return self.chroma_db.add_multiple_requirements(contents, source)
    
    def get_context_provider(self) -> RequirementContextProvider:
        """
        Get the context provider instance.
        
        Returns:
            RequirementContextProvider instance
        """
        return self.context_provider
