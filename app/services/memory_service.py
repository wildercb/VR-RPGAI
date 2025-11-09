"""Memory service using Mem0 for semantic memory management."""
from mem0 import Memory
from typing import List, Dict, Optional
from app.config import settings
from loguru import logger
import json


class MemoryService:
    """
    Wrapper for Mem0 memory management.

    Provides:
    - Character-specific memory (what the character remembers about users)
    - User-global memory (facts that persist across all characters)
    - Semantic retrieval of relevant memories for context
    """

    _instance = None
    _memory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._memory is None:
            self._initialize_mem0()

    def _initialize_mem0(self):
        """Initialize Mem0 with Ollama LLM and PostgreSQL vector store."""
        config = {
            "llm": {
                "provider": settings.MEM0_LLM_PROVIDER,
                "config": {
                    "model": settings.MEM0_MODEL,
                    "temperature": 0.1,
                    "max_tokens": 2000,
                }
            },
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "user": settings.DATABASE_USER,
                    "password": settings.DATABASE_PASSWORD,
                    "host": settings.DATABASE_HOST,
                    "port": settings.DATABASE_PORT,
                    "dbname": settings.DATABASE_NAME,
                }
            },
            "version": "v1.1"
        }

        # Add embedder config if using non-OpenAI LLM
        if settings.MEM0_LLM_PROVIDER == "ollama":
            config["embedder"] = {
                "provider": "ollama",
                "config": {
                    "model": "nomic-embed-text:latest",
                    "ollama_base_url": settings.OLLAMA_BASE_URL
                }
            }
            # Also set ollama_base_url for LLM
            config["llm"]["config"]["ollama_base_url"] = settings.OLLAMA_BASE_URL

        # Add OpenRouter specific config
        if settings.MEM0_LLM_PROVIDER == "openrouter":
            config["llm"]["config"]["base_url"] = "https://openrouter.ai/api/v1"
            config["llm"]["config"]["api_key"] = settings.OPENROUTER_API_KEY

        logger.info(f"Initializing Mem0 with {settings.MEM0_LLM_PROVIDER} LLM and pgvector")
        self._memory = Memory.from_config(config)
        logger.info("Mem0 initialized successfully")

    def add_character_memory(
        self,
        character_id: str,
        user_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Add memories from a conversation for a specific character.

        Args:
            character_id: ID of the character
            user_id: ID of the user
            messages: List of conversation messages [{"role": "user", "content": "..."}]
            metadata: Optional metadata (e.g., conversation_id, timestamp)

        Returns:
            List of extracted memories
        """
        # Mem0 uses user_id and agent_id to organize memories
        agent_id = f"character_{character_id}"

        meta = metadata or {}
        meta["character_id"] = character_id

        try:
            result = self._memory.add(
                messages=messages,
                user_id=user_id,
                agent_id=agent_id,
                metadata=meta
            )
            logger.info(f"Added {len(result.get('results', []))} memories for character {character_id}, user {user_id}")
            return result.get('results', [])
        except Exception as e:
            logger.error(f"Error adding memories: {e}")
            return []

    def get_character_memories(
        self,
        character_id: str,
        user_id: str,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve relevant memories for a character about a specific user.

        Args:
            character_id: ID of the character
            user_id: ID of the user
            query: Optional query to filter relevant memories semantically
            limit: Maximum number of memories to retrieve

        Returns:
            List of relevant memories
        """
        agent_id = f"character_{character_id}"

        try:
            if query:
                # Semantic search for relevant memories
                result = self._memory.search(
                    query=query,
                    user_id=user_id,
                    agent_id=agent_id,
                    limit=limit
                )
            else:
                # Get all memories for this user
                result = self._memory.get_all(
                    user_id=user_id,
                    agent_id=agent_id,
                    limit=limit
                )

            memories = result.get('results', [])
            logger.info(f"Retrieved {len(memories)} memories for character {character_id}, user {user_id}")
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []

    def get_user_global_memories(
        self,
        user_id: str,
        query: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve user memories that span across all characters.

        Args:
            user_id: ID of the user
            query: Optional query for semantic search
            limit: Maximum number of memories

        Returns:
            List of user-global memories
        """
        try:
            if query:
                result = self._memory.search(
                    query=query,
                    user_id=user_id,
                    limit=limit
                )
            else:
                result = self._memory.get_all(
                    user_id=user_id,
                    limit=limit
                )

            memories = result.get('results', [])
            logger.info(f"Retrieved {len(memories)} global memories for user {user_id}")
            return memories
        except Exception as e:
            logger.error(f"Error retrieving global memories: {e}")
            return []

    def update_memory(self, memory_id: str, data: str) -> Dict:
        """
        Update an existing memory.

        Args:
            memory_id: ID of the memory to update
            data: New memory content

        Returns:
            Update result
        """
        try:
            result = self._memory.update(memory_id=memory_id, data=data)
            logger.info(f"Updated memory {memory_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return {}

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        try:
            self._memory.delete(memory_id=memory_id)
            logger.info(f"Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def delete_all_character_memories(self, character_id: str, user_id: str) -> bool:
        """Delete all memories for a character-user pair."""
        agent_id = f"character_{character_id}"

        try:
            self._memory.delete_all(user_id=user_id, agent_id=agent_id)
            logger.info(f"Deleted all memories for character {character_id}, user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memories: {e}")
            return False

    def get_memory_history(
        self,
        character_id: str,
        user_id: str
    ) -> List[Dict]:
        """Get full memory history for a character-user interaction."""
        agent_id = f"character_{character_id}"

        try:
            result = self._memory.history(user_id=user_id, agent_id=agent_id)
            return result.get('results', [])
        except Exception as e:
            logger.error(f"Error getting memory history: {e}")
            return []


# Global singleton instance
memory_service = MemoryService()
