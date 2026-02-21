"""
SQLAlchemy ORM models for TetraploidSNPMap.

Defines the core database tables: Project, Dataset, AnalysisJob and TraitData.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.models.db import Base


class ProjectMode(str, enum.Enum):
    """Operating mode for a TetraploidSNPMap project."""

    SNP = "SNP"
    QTL = "QTL"
    NONSNP = "NONSNP"


class AnalysisStatus(str, enum.Enum):
    """Lifecycle status of an analysis job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Project(Base):
    """A TetraploidSNPMap project containing datasets and analyses."""

    __tablename__ = "projects"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(255), nullable=False)
    mode: str = Column(Enum(ProjectMode), nullable=False, default=ProjectMode.SNP)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    datasets = relationship(
        "Dataset", back_populates="project", cascade="all, delete-orphan"
    )
    analysis_jobs = relationship(
        "AnalysisJob", back_populates="project", cascade="all, delete-orphan"
    )
    trait_data = relationship(
        "TraitData", back_populates="project", cascade="all, delete-orphan"
    )


class Dataset(Base):
    """An imported dataset (SNPloc, non-SNP marker file, etc.)."""

    __tablename__ = "datasets"

    id: int = Column(Integer, primary_key=True, index=True)
    project_id: int = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: str = Column(String(255), nullable=False)
    file_path: str = Column(String(512), nullable=False)
    type: str = Column(String(50), nullable=False)  # e.g. "snploc", "qua", "loc"
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="datasets")
    analysis_jobs = relationship("AnalysisJob", back_populates="dataset")
    trait_data = relationship("TraitData", back_populates="dataset")


class AnalysisJob(Base):
    """A submitted (or completed) analysis job."""

    __tablename__ = "analysis_jobs"

    id: int = Column(Integer, primary_key=True, index=True)
    project_id: int = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Optional[int] = Column(
        Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    analysis_type: str = Column(String(50), nullable=False)
    status: str = Column(
        Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING
    )
    params_json: Optional[str] = Column(Text, nullable=True)
    result_path: Optional[str] = Column(String(512), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    error_message: Optional[str] = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="analysis_jobs")
    dataset = relationship("Dataset", back_populates="analysis_jobs")


class TraitData(Base):
    """Imported trait / QUA data associated with a project."""

    __tablename__ = "trait_data"

    id: int = Column(Integer, primary_key=True, index=True)
    project_id: int = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Optional[int] = Column(
        Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    file_path: str = Column(String(512), nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="trait_data")
    dataset = relationship("Dataset", back_populates="trait_data")
