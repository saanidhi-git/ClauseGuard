"""Request bodies for the API."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

DocType = Literal["rental", "offer_letter", "tos", "auto"]


class TextIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=200_000)
    doc_type: DocType = "auto"
    title: Optional[str] = Field(None, max_length=200)


class AskIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)


class ClassifyIn(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000)
