import enum
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Enum, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class EmailStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    EXTRACTING = "EXTRACTING"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    READY_TO_CONFIRM = "READY_TO_CONFIRM"
    CONFIRMATION_SENT = "CONFIRMATION_SENT"
    ORDER_CREATED = "ORDER_CREATED"
    FAILED = "FAILED"

class EmailMessage(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    from_email: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(500), default="")
    body_text: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    status: Mapped[EmailStatus] = mapped_column(Enum(EmailStatus), default=EmailStatus.RECEIVED)
    extracted: Mapped[dict] = mapped_column(JSON, default=dict)
    missing_fields: Mapped[list] = mapped_column(JSON, default=list)
    last_error: Mapped[str] = mapped_column(Text, default="")

    order = relationship("Order", back_populates="email", uselist=False)

class ExtractionRun(Base):
    __tablename__ = "extraction_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), index=True)
    layer: Mapped[str] = mapped_column(String(50))  # regex | gemini | human
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    output_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), unique=True)

    customer_name: Mapped[str] = mapped_column(String(255))
    weight_kg: Mapped[int] = mapped_column(Integer)
    pickup_location: Mapped[str] = mapped_column(String(500))
    drop_location: Mapped[str] = mapped_column(String(500))
    pickup_time_window: Mapped[str] = mapped_column(String(255))

    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    email = relationship("EmailMessage", back_populates="order")

class HumanReview(Base):
    __tablename__ = "human_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), unique=True)
    reviewer: Mapped[str] = mapped_column(String(255), default="")
    proposed_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    patterns: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class AgentState(Base):
    __tablename__ = "agent_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)