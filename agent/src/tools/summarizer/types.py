from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class SummarizerRequest(BaseModel):
    title: Optional[str] = Field(None, description="Title of the content to summarize.")
    description: Optional[str] = Field(None, description="Description or extracted text metadata.")
    vision_analysis: Optional[str] = Field(None, description="Vision description or OCR text.")
    transcript: Optional[str] = Field(None, description="Video or audio transcript.")

class SummarizerResponse(BaseModel):
    summary: str = Field(..., description="A concise 2-sentence summary of the content.")

    @field_validator('summary')
    @classmethod
    def validate_two_sentences(cls, v: str) -> str:
        # Simple sentence count based on punctuation
        sentences = re.split(r'(?<=[.!?])\s+', v.strip())
        if len(sentences) > 2:
            return " ".join(sentences[:2])
        return v
