from pipecat.processors.base_processor import BaseProcessor
from pipecat.frames.frames import TextFrame
from rag.retriever import retrieve_context
import logging

logger = logging.getLogger(__name__)

class RAGProcessor(BaseProcessor):
    """
    Processor that augments user queries with relevant context from the knowledge base.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        # Only process text frames from user input
        if isinstance(frame, TextFrame) and direction == "user_to_llm":
            user_query = frame.text

            # Retrieve context from the knowledge base
            try:
                context = retrieve_context(user_query)
                logger.info(f"RAG activated for query: '{user_query[:100]}...' - Retrieved {len(context)} characters of context")
                logger.debug(f"RAG retrieved context: {context[:200]}...")

                # Create RAG-augmented prompt
                rag_prompt = f"""
Based on the following context from our knowledge base:

{context}

Please answer the user's question: {user_query}

Answer using only the information from the context above. If the context doesn't contain enough information to answer the question, say so.
"""

                # Replace the original text with the RAG-augmented prompt
                frame.text = rag_prompt
                logger.info("RAG context successfully added to user query")

            except Exception as e:
                logger.error(f"RAG processing failed for query '{user_query[:100]}...': {e}")
                # If RAG fails, continue with original query
                pass

        # Pass the frame along
        await self.push_frame(frame, direction)