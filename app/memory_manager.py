"""
Memory Manager for Sidekick
This module handles long-term memory storage and retrieval using ChromaDB.

How it works:
1. Conversations are processed to extract important facts
2. Facts are converted to embeddings (vector representations)
3. ChromaDB stores these embeddings for fast similarity search
4. When needed, we can query for relevant memories
"""

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from typing import List, Dict, Any
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)


class MemoryManager:
    """
    Manages long-term memory storage and retrieval for Sidekick.
    
    Key Concepts:
    - Embeddings: Convert text into numbers (vectors) that represent meaning
    - Vector Database: Store and search embeddings by similarity
    - Metadata: Additional info about each memory (timestamp, source, etc.)
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the memory manager.
        
        Args:
            persist_directory: Where to save the database on disk
                              (persists between sessions!)
        """
        self.persist_directory = persist_directory
        
        # Create embeddings model - converts text to vectors
        # Using HuggingFace's free local embeddings (completely free!)
        # Model: all-MiniLM-L6-v2 - fast, small, and good quality
        # Runs 100% locally on your machine - no API calls needed!
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize ChromaDB vector store
        # This creates/loads a persistent database
        self.vectorstore = Chroma(
            collection_name="sidekick_memories",
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
        
        print(f"✅ Memory Manager initialized. Database at: {persist_directory}")
    
    def store_memory(
        self, 
        content: str, 
        memory_type: str = "fact",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store a piece of information in long-term memory.
        
        Args:
            content: The information to remember (e.g., "User prefers Python")
            memory_type: Category (fact, preference, task, instruction)
            metadata: Extra info (source, importance, etc.)
        
        Returns:
            memory_id: Unique ID for this memory
        """
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "memory_type": memory_type,
        })
        
        # Create a document (LangChain's way of representing text + metadata)
        doc = Document(
            page_content=content,
            metadata=metadata
        )
        
        # Add to vector database
        # This automatically:
        # 1. Creates embeddings for the content
        # 2. Stores in ChromaDB
        # 3. Persists to disk
        ids = self.vectorstore.add_documents([doc])
        
        print(f"💾 Stored memory: {content[:50]}... (ID: {ids[0]})")
        return ids[0]
    
    def recall_memories(
        self, 
        query: str, 
        k: int = 5,
        memory_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on a query.
        
        How it works:
        1. Convert query to embedding
        2. Find most similar memories using vector similarity
        3. Return top k results
        
        Args:
            query: What to search for (e.g., "user's programming preferences")
            k: How many memories to return
            memory_type: Filter by type (optional)
        
        Returns:
            List of memories with content and metadata
        """
        # Build filter if memory_type specified
        filter_dict = {"memory_type": memory_type} if memory_type else None
        
        # Similarity search - this is the magic!
        # ChromaDB finds vectors closest to query vector
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )
        
        # Format results
        memories = []
        for doc, score in results:
            memories.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": score,  # Lower = more similar
            })
        
        if memories:
            print(f"🧠 Recalled {len(memories)} relevant memories for: {query[:50]}...")
        
        return memories
    
    def store_conversation_facts(
        self, 
        conversation_summary: str,
        facts: List[str]
    ):
        """
        Store multiple facts from a conversation.
        
        Args:
            conversation_summary: Brief summary of the conversation
            facts: List of extracted facts to remember
        """
        for fact in facts:
            self.store_memory(
                content=fact,
                memory_type="fact",
                metadata={"source": conversation_summary}
            )
    
    def get_memory_context(self, current_task: str) -> str:
        """
        Get relevant memories formatted as context for the LLM.
        
        Args:
            current_task: What the user is currently asking about
        
        Returns:
            Formatted string with relevant memories
        """
        memories = self.recall_memories(current_task, k=5)
        
        if not memories:
            return "No relevant memories found."
        
        context = "📚 Relevant information from previous conversations:\n\n"
        for i, memory in enumerate(memories, 1):
            timestamp = memory["metadata"].get("timestamp", "Unknown time")
            content = memory["content"]
            context += f"{i}. {content} (from {timestamp})\n"
        
        return context
    
    def clear_all_memories(self):
        """
        ⚠️ Delete all stored memories. Use with caution!
        """
        # Delete the collection and recreate
        self.vectorstore.delete_collection()
        self.vectorstore = Chroma(
            collection_name="sidekick_memories",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        print("🗑️ All memories cleared.")

