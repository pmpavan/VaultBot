from typing import Optional, List
from pydantic import BaseModel, Field
from .taxonomy import CategoryEnum, PriceRangeEnum

class NormalizerRequest(BaseModel):
    title: str = Field(..., description="The title of the content")
    description: Optional[str] = Field(None, description="The description or summary of the content")
    raw_content: Optional[str] = Field(None, description="Any additional raw text content")
    source_url: str = Field(..., description="The source URL of the content")

class NormalizerResponse(BaseModel):
    category: CategoryEnum = Field(..., description="The primary category of the content")
    price_range: Optional[PriceRangeEnum] = Field(None, description="The price range of the content, if applicable")
    tags: List[str] = Field(..., description="A list of 3-7 semantic tags describing the content", min_items=1, max_items=10)
