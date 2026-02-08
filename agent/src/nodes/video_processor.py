"""
LangGraph node for video processing.
Integrates video frame extraction and analysis into the agent workflow.
"""

from typing import TypedDict, Any, Optional
from tools.video import VideoProcessingService, VideoProcessingRequest


from langgraph.graph import StateGraph, END

class VideoProcessorState(TypedDict):
    """State for video processor node."""
    job_id: str
    video_url: str
    message_id: str
    auth_token: Optional[str]
    account_sid: Optional[str]
    video_summary: Optional[str]
    error: Optional[str]


class VideoProcessorNode:
    """
    LangGraph node for processing videos.
    Downloads video, extracts frames, analyzes with Vision API, and generates summary.
    """

    def __init__(self, num_frames: int = 5):
        """
        Initialize the video processor node.
        
        Args:
            num_frames: Number of frames to extract from each video
        """
        self.service = VideoProcessingService(num_frames=num_frames)

    def __call__(self, state: VideoProcessorState) -> VideoProcessorState:
        """
        Process video from state.
        
        Args:
            state: Current state containing video_url and message_id
            
        Returns:
            Updated state with video_summary or error
        """
        try:
            # Create processing request
            request = VideoProcessingRequest(
                video_url=state["video_url"],
                message_id=state["message_id"],
                auth_token=state.get("auth_token"),
                account_sid=state.get("account_sid")
            )
            
            # Process video
            response = self.service.process_video(request)
            
            # Update state with summary
            return {
                **state,
                "video_summary": response.summary,
                "error": None
            }
            
        except Exception as e:
            # Handle errors gracefully
            return {
                **state,
                "video_summary": None,
                "error": f"Video processing failed: {str(e)}"
            }


def create_video_processor_graph(num_frames: int = 5):
    """Create and compile the video processor graph."""
    node = VideoProcessorNode(num_frames=num_frames)
    
    workflow = StateGraph(VideoProcessorState)
    
    # Add the node
    workflow.add_node("processor", node)
    
    # Set entry point
    workflow.set_entry_point("processor")
    
    # Set finish point
    workflow.add_edge("processor", END)
    
    # Compile
    return workflow.compile()

# Legacy factory for backward compatibility
def create_video_processor_node(num_frames: int = 5) -> VideoProcessorNode:
    """
    Create a video processor node instance.
    (Legacy factory)
    """
    return VideoProcessorNode(num_frames=num_frames)
