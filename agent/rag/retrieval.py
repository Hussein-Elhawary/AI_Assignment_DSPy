import os
import re
from typing import List, Dict
from rank_bm25 import BM25Okapi


class LocalRetriever:
    """Retriever for local markdown documentation using BM25."""
    
    def __init__(self, docs_path: str = "docs/"):
        """
        Initialize the retriever with a path to documentation folder.
        
        Args:
            docs_path: Path to folder containing .md files
        """
        self.docs_path = docs_path
        self.chunks = []
        self.bm25 = None
        self._load_and_index_docs()
    
    def _load_and_index_docs(self):
        """Load markdown files and create BM25 index."""
        if not os.path.exists(self.docs_path):
            print(f"Warning: Documentation path '{self.docs_path}' does not exist.")
            return
        
        # Load all .md files
        for filename in os.listdir(self.docs_path):
            if filename.endswith('.md'):
                filepath = os.path.join(self.docs_path, filename)
                self._load_file(filepath, filename)
        
        # Create BM25 index
        if self.chunks:
            tokenized_chunks = [self._tokenize(chunk['content']) for chunk in self.chunks]
            self.bm25 = BM25Okapi(tokenized_chunks)
    
    def _load_file(self, filepath: str, filename: str):
        """
        Load and chunk a single markdown file.
        
        Args:
            filepath: Full path to the file
            filename: Name of the file (for doc_id)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chunk the content
            file_chunks = self._chunk_content(content, filename)
            self.chunks.extend(file_chunks)
            
        except Exception as e:
            print(f"Error loading file {filepath}: {str(e)}")
    
    def _chunk_content(self, content: str, filename: str) -> List[Dict[str, str]]:
        """
        Chunk content by markdown headers (##) or double newlines.
        
        Args:
            content: File content to chunk
            filename: Name of the file
            
        Returns:
            List of chunks with doc_id and content
        """
        chunks = []
        
        # Try splitting by markdown headers first
        header_pattern = r'\n##\s+'
        sections = re.split(header_pattern, content)
        
        # If no headers found, split by double newlines
        if len(sections) <= 1:
            sections = content.split('\n\n')
        
        for idx, section in enumerate(sections):
            section = section.strip()
            if section:  # Skip empty chunks
                doc_id = f"{filename}::chunk_{idx}"
                chunks.append({
                    "doc_id": doc_id,
                    "content": section
                })
        
        return chunks
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\w+', text.lower())
        return tokens
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, str]]:
        """
        Search for relevant chunks using BM25.
        
        Args:
            query: Search query
            k: Number of top results to return
            
        Returns:
            List of dictionaries with 'doc_id' and 'content' keys
        """
        if not self.bm25 or not self.chunks:
            return []
        
        # Tokenize query
        tokenized_query = self._tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        # Return top k chunks
        results = []
        for idx in top_indices:
            results.append({
                "doc_id": self.chunks[idx]["doc_id"],
                "content": self.chunks[idx]["content"]
            })
        
        return results
