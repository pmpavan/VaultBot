"""
LangGraph node for article processing.
Integrates article extraction and classification into the agent workflow.
"""

import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from tools.article.service import ArticleService
from tools.article.types import ArticleExtractionRequest, ArticleContentType

logger = logging.getLogger(__name__)

class ArticleProcessorState(TypedDict):
    """State for article processor node."""
    job_id: str
    url: str
    content_type_hint: Optional[ArticleContentType]
    
    # Results
    text: Optional[str]
    title: Optional[str]
    author: Optional[str]
    publish_date: Optional[str]
    site_name: Optional[str]
    metadata: Optional[dict]
    og_tags: Optional[dict]
    content_type: Optional[ArticleContentType]
    is_paywall: bool
    
    error: Optional[str]

class ArticleProcessorNode:
    """
    LangGraph node for processing articles.
    Extracts text, metadata, and classifies content.
    """

    def __init__(self):
        self.article_service = ArticleService()

    def __call__(self, state: ArticleProcessorState) -> ArticleProcessorState:
        """
        Process article from state.
        
        Args:
            state: Current state containing url
            
        Returns:
            Updated state with extracted text and metadata
        """
        try:
            url = state["url"]
            logger.info(f"Processing article job for URL: {url}")

            # Create Request
            request = ArticleExtractionRequest(
                url=url,
                content_type_hint=state.get("content_type_hint")
            )
            
            # Execute Service
            response = self.article_service.extract(request)
            
            # Update State
            return {
                **state,
                "text": response.text,
                "title": response.title,
                "author": response.author,
                "publish_date": response.publish_date,
                "site_name": response.site_name,
                "metadata": response.metadata,
                "og_tags": response.og_tags,
                "content_type": response.content_type,
                "is_paywall": response.is_paywall,
                "error": None
            }

        except Exception as e:
            logger.error(f"Article processing failed: {e}", exc_info=True)
            return {
                **state,
                "text": None,
                "error": f"Article processing failed: {str(e)}"
            }

def create_article_processor_graph():
    """Create and compile the article processing graph."""
    node = ArticleProcessorNode()
    
    workflow = StateGraph(ArticleProcessorState)
    
    # Add the node
    workflow.add_node("processor", node)
    
    # Set entry point
    workflow.set_entry_point("processor")
    
    # Set finish point
    workflow.add_edge("processor", END)
    
    # Compile
    return workflow.compile()
