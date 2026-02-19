from typing import Dict, Any, List, Optional
from pydantic import Field, BaseModel
from .core import VaultBotJsonSystemPrompt, BasePrompt

class SummarizerResponse(BaseModel):
    """Temporary schema for prompt definition until tools/summarizer/types.py is created"""
    summary: str = Field(..., description="A concise 2-sentence summary of the content.")

class SummarizerSystemPrompt(VaultBotJsonSystemPrompt):
    """
    System prompt for the Natural Language Summary Generator.
    """
    name: str = "summarizer_system"
    description: str = "System instructions for generating concise keyword-dense summaries."
    
    summarizer_instructions: List[str] = Field(
        default=[
            "Generate a CONCISE 2-sentence summary of the provided content.",
            "Sentence 1: Focus on the 'What' and 'Who' (e.g., 'A video of a high-end sushi restaurant in Kyoto').",
            "Sentence 2: Focus on unique details or context (e.g., 'Known for live jazz and seasonal omakase').",
            "Maintain factual strictness. DO NOT hallucinate details not found in the input.",
            "Make it keyword-dense to aid future natural language search (RAG).",
            "Handle missing metadata gracefully by summarizing whatever is available.",
            "The output MUST be natural language, not a list of keywords."
        ],
        description="Specific instructions for summarization"
    )

    output_schema: Dict[str, Any] = Field(
        default_factory=SummarizerResponse.model_json_schema,
        description="The JSON schema the output must adhere to"
    )

    def compile(self, **kwargs) -> str:
        """
        Compiles the prompt into a JSON string.
        """
        return self.model_dump_json(include={
            "persona_role",
            "persona_goal",
            "persona_rules",
            "format_rules",
            "summarizer_instructions",
            "output_schema"
        })

class SummarizerUserPrompt(BasePrompt):
    """
    User prompt for passing content to be summarized.
    """
    name: str = "summarizer_user"
    description: str = "Formats inputs for the summarizer."

    def compile(self, **kwargs) -> str:
        """
        Args:
            title (str): Title of the content.
            description (str): Description or raw text.
            vision_analysis (str): OCR or visual description.
            transcript (str): Video/Audio transcript.
        """
        parts = []
        if kwargs.get("title"):
            parts.append(f"Title: {kwargs['title']}")
        if kwargs.get("description"):
            parts.append(f"Description/Metadata: {kwargs['description']}")
        if kwargs.get("vision_analysis"):
            parts.append(f"Visual/OCR Analysis: {kwargs['vision_analysis']}")
        if kwargs.get("transcript"):
            parts.append(f"Transcript: {kwargs['transcript']}")
            
        if not parts:
            return "No content provided to summarize. Please return an error message."
            
        return "\n".join(parts) + "\n\nGenerate the 2-sentence summary."
