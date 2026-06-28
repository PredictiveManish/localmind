"""Pydantic models for structured data."""
from typing import List, Optional
from pydantic import BaseModel, Field


class CPUInfo(BaseModel):
    """CPU details."""
    name: str
    physical_cores: int
    logical_cores: int
    max_frequency_mhz: float


class RAMInfo(BaseModel):
    """RAM details."""
    total_gb: float
    available_gb: float
    


class GPUInfo(BaseModel):
    """GPU details if available."""
    name: str
    vram_mb: int
    driver_version: Optional[str] = None
    vendor: str = ""  # NVIDIA, AMD, Intel, Apple
    is_unified_memory: bool = False  # macOS Apple Silicon or Intel iGPU sharing RAM


class StorageInfo(BaseModel):
    """Root disk info."""
    total_gb: float
    used_gb: float
    free_gb: float


class HardwareReport(BaseModel):
    """Complete hardware snapshot."""
    os: str
    cpu: CPUInfo
    ram: RAMInfo
    gpus: List[GPUInfo] = Field(default_factory=list)
    storage: StorageInfo


class MachineClass(BaseModel):
    """Hardware tier classification."""
    tier: str                     # Tiny, Entry, Midrange, High-End, Enthusiast
    rationale: str
    recommended_param_range: str  # e.g. "1B-4B"


class ModelRecommendation(BaseModel):
    """Specific model suggestion."""
    name: str
    parameter_size: str
    notes: str


class DoctorReport(BaseModel):
    """Full diagnostic report."""
    hardware: HardwareReport
    classification: MachineClass
    warnings: List[str]
    recommendations: List[ModelRecommendation]


class OllamaModel(BaseModel):
    """Metadata for an Ollama model."""
    name: str
    description: str
    pulls: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    size: Optional[str] = None