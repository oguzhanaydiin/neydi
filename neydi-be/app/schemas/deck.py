import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import UserRole


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    front: str
    back: str
    confidence: int


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    cards: list[CardOut] = []
    # Read from the ORM's created_at_ms attribute, serialise as camelCase key.
    createdAt: int = Field(validation_alias="created_at_ms")


class DeckOwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    role: UserRole


class DeckPublicOut(BaseModel):
    """Deck shape returned by the public /decks/explore endpoint. Includes owner info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    cards: list[CardOut] = []
    createdAt: int = Field(validation_alias="created_at_ms")
    owner: DeckOwnerOut


class CardIn(BaseModel):
    id: Optional[uuid.UUID] = None
    front: str
    back: str
    confidence: int = 0


class DeckIn(BaseModel):
    """Used for POST /decks and PUT /decks/{id}. Accepts client-generated UUIDs."""

    id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    cards: list[CardIn] = []
    createdAt: Optional[int] = None


class DeckPatch(BaseModel):
    name: str
    description: Optional[str] = None


class CardPatch(BaseModel):
    front: str
    back: str


class ConfidencePatch(BaseModel):
    confidence: int

    @field_validator("confidence")
    @classmethod
    def clamp(cls, v: int) -> int:
        return max(0, min(5, v))


class ReorderPatch(BaseModel):
    order: list[uuid.UUID]
