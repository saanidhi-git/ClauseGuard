# Database tables

from datetime import datetime, timezone
from typing import Iterator, List, Optional

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Session, SQLModel, create_engine

from .config import DB_PATH


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    doc_type: str
    filename: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    status: str = "done"
    error: Optional[str] = None
    score: int = 0
    verdict: str = ""
    level_counts: dict = Field(default_factory=dict, sa_column=Column(JSON))
    key_facts: dict = Field(default_factory=dict, sa_column=Column(JSON))
    summary: list = Field(default_factory=list, sa_column=Column(JSON))
    model_used: str = ""
    page_count: int = 0


class Clause(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(index=True, foreign_key="document.id")
    idx: int
    number: str = ""
    heading: str = ""
    text: str = Field(sa_column=Column(Text))
    page: int = 1
    labels: list = Field(default_factory=list, sa_column=Column(JSON))
    probs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    risk_level: str = "Safe"
    risk_score: float = 0.0
    explanation: dict = Field(default_factory=dict, sa_column=Column(JSON))


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(index=True, foreign_key="document.id")
    role: str
    content: str = Field(sa_column=Column(Text))
    cited_clause_ids: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_now)


class LlmCache(SQLModel, table=True):
    hash: str = Field(primary_key=True)
    response: str = Field(sa_column=Column(Text))


DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


# keep times in UTC
def iso(dt: datetime) -> str:
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()
