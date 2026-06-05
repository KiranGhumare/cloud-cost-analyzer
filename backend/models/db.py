import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    services: Mapped[list] = mapped_column(JSON)
    total_savings_usd: Mapped[float] = mapped_column(Float, default=0.0)
    llm_provider: Mapped[str] = mapped_column(String(50))

    findings: Mapped[list["Finding"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_runs.id")
    )
    service: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[str] = mapped_column(String(255))
    resource_type: Mapped[str] = mapped_column(String(100))
    finding_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1000))
    estimated_monthly_savings_usd: Mapped[float] = mapped_column(Float)
    confidence: Mapped[str] = mapped_column(String(20))
    recommendation: Mapped[str] = mapped_column(String(1000))
    finding_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="open")
    actioned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    run: Mapped["AnalysisRun"] = relationship(back_populates="findings")
