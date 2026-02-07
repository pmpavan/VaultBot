from typing import List, Optional
from pydantic import Field
from .core import BasePrompt, VaultBotJsonSystemPrompt

class VisionAnalyzePrompt(BasePrompt):
    """
    Prompt for analyzing images using Vision APIs.
    """
    name: str = "vision_analyze"
    description: str = "Analyzes an image based on a user instruction."
    
    instruction: str = Field(..., description="User instruction for analysis")
    
    def compile(self, **kwargs) -> str:
        """
        Compiles the prompt message into a JSON string.
        """
        return self.model_dump_json(include={"instruction"})

class VisionSystemPrompt(VaultBotJsonSystemPrompt):
    """
    System prompt for Vision tasks.
    Inherits VaultBot persona and JSON enforcement.
    Adds vision-specific instructions.
    """
    name: str = "vision_system"
    description: str = "System instructions for Vision API tasks."
    
    vision_instructions: List[str] = Field(
        default=[
            "Analyze the provided image deeply. Identify objects, text, location clues, and general 'vibe'.",
            "If the image contains text, extract it accurately.",
            "If the image is a location/place, try to identify the type (e.g., Cafe, Bar, Park).",
            "Adhere strictly to the requested analysis scope."
        ],
        description="Specific instructions for vision capabilities"
    )
    
    def compile(self, **kwargs) -> str:
        # Return the entire object (Persona + Format Rules + Vision Instructions) as a JSON string
        return self.model_dump_json(include={
            "persona_role", 
            "persona_goal", 
            "persona_rules", 
            "format_rules", 
            "vision_instructions"
        })
