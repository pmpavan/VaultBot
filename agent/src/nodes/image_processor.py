"""
LangGraph node for image processing.
Integrates image extraction and analysis into the agent workflow.
"""

import base64
import logging
from typing import TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, END

from tools.image.service import ImageExtractorService
from tools.image.types import ImageExtractionRequest
from tools.vision.service import VisionService
from tools.vision.types import VisionRequest

logger = logging.getLogger(__name__)

class ImageProcessorState(TypedDict):
    """State for image processor node."""
    job_id: str
    url: str
    message_id: str
    platform_hint: Optional[str]
    image_summary: Optional[str]
    error: Optional[str]
    metadata: Optional[dict]

class ImageProcessorNode:
    """
    LangGraph node for processing images.
    Extracts images from URL, analyzes with Vision API, and generates summary.
    """

    def __init__(self):
        self.extractor_service = ImageExtractorService()
        self.vision_service = VisionService()

    def __call__(self, state: ImageProcessorState) -> ImageProcessorState:
        """
        Process image from state.
        
        Args:
            state: Current state containing url
            
        Returns:
            Updated state with image_summary and metadata
        """
        try:
            url = state["url"]
            logger.info(f"Processing image job for URL: {url}")

            # Step 1: Extract images
            request = ImageExtractionRequest(
                url=url,
                platform_hint=state.get("platform_hint"),
                message_id=state.get("message_id")
            )
            extraction_response = self.extractor_service.extract(request)
            
            # Step 2: Analyze images with Vision API
            vision_descriptions = []
            
            # Limit number of images to analyze to prevent timeouts/OOM
            MAX_IMAGES = 5
            images_to_process = extraction_response.images[:MAX_IMAGES]
            
            from PIL import Image
            import io

            for i, image_bytes in enumerate(images_to_process):
                try:
                    # Resize image if too large to save memory and token checking
                    with Image.open(io.BytesIO(image_bytes)) as img:
                        # Convert to RGB if needed
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                            
                        # Resize if larger than 1024x1024 (good enough for vision)
                        max_size = (1024, 1024)
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # Save to buffer
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=85)
                        processed_bytes = buffer.getvalue()

                    # Convert to base64
                    image_base64 = base64.b64encode(processed_bytes).decode('utf-8')
                    image_data_url = f"data:image/jpeg;base64,{image_base64}"
                    
                    # Create vision request
                    vision_request = VisionRequest(
                        image_input=image_data_url,
                        prompt="Describe this image in detail and extract key information (text, objects, context). Focus on being thorough and identifying specific details.",
                        model_provider="openai"
                    )
                    
                    vision_response = self.vision_service.analyze(vision_request)
                    
                    # Extract description
                    analysis_data = vision_response.analysis_data
                    description = self._extract_description(analysis_data)
                    vision_descriptions.append(description)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze image {i+1}: {e}")
                    vision_descriptions.append(f"[Analysis Failed: {str(e)}]")
            
            # Step 3: Aggregate results
            summary = self._aggregate_results(extraction_response.metadata, vision_descriptions)
            
            return {
                **state,
                "image_summary": summary,
                "metadata": extraction_response.metadata,
                "error": None
            }

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                **state,
                "image_summary": None,
                "error": f"Image processing failed: {str(e)}"
            }

    def _extract_description(self, analysis_data: Any) -> str:
        """Helper to extract description from analysis data."""
        if isinstance(analysis_data, dict):
            if 'description' in analysis_data:
                return analysis_data['description']
            elif 'content' in analysis_data:
                return analysis_data['content']
        return str(analysis_data)

    def _aggregate_results(self, metadata: dict, vision_descriptions: List[str]) -> str:
        """Combine platform metadata and vision descriptions."""
        parts = []
        
        # Add Platform Context
        if metadata.get('caption'):
            parts.append(f"Caption: {metadata['caption']}")
        
        if metadata.get('author'):
            parts.append(f"Author: {metadata['author']}")
            
        # Add Visual Descriptions
        if vision_descriptions:
            if len(vision_descriptions) == 1:
                parts.append(f"Visual Content: {vision_descriptions[0]}")
            else:
                parts.append("Visual Content:")
                for i, desc in enumerate(vision_descriptions, 1):
                    parts.append(f"Image {i}: {desc}")
                    
        return "\n".join(parts)


def create_image_processor_graph():
    """Create and compile the image processing graph."""
    node = ImageProcessorNode()
    
    workflow = StateGraph(ImageProcessorState)
    
    # Add the node
    workflow.add_node("processor", node)
    
    # Set entry point
    workflow.set_entry_point("processor")
    
    # Set finish point
    workflow.add_edge("processor", END)
    
    # Compile
    return workflow.compile()

# Legacy factory for backward compatibility if needed, but we should use the graph
def create_image_processor_node() -> ImageProcessorNode:
    """Factory function for creating the node."""
    return ImageProcessorNode()

