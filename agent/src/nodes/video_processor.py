"""
LangGraph node for video processing.
Integrates video frame extraction and analysis into the agent workflow.
"""

from typing import TypedDict, Any
from tools.video import VideoProcessingService, VideoProcessingRequest


class VideoProcessorState(TypedDict):
    """State for video processor node."""
    job_id: str
    video_url: str
    message_id: str
    auth_token: str | None
    video_summary: str | None
    error: str | None


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
                auth_token=state.get("auth_token")
            )
            
            # Process video
            response = self.service.process_video(request)
            
            # NOTE (AC 6): Database persistence handled by orchestrator/worker layer
            # This node follows the separation of concerns pattern (see worker.py):
            # - Nodes are pure: process state and return updated state
            # - Orchestrator/worker persists results to database
            # The video_worker.py (or extended worker.py) will:
            # 1. Call this node to get video_summary in state
            # 2. Persist summary to jobs table (result JSONB field or payload)
            # 3. Update job status to 'complete'
            
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


# Factory function for creating the node
def create_video_processor_node(num_frames: int = 5) -> VideoProcessorNode:
    """
    Create a video processor node instance.
    
    Args:
        num_frames: Number of frames to extract
        
    Returns:
        VideoProcessorNode instance
    """
    return VideoProcessorNode(num_frames=num_frames)
