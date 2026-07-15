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
    """Metadata for an Ollama library model (remote)."""
    name: str
    description: str
    pulls: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    size: Optional[str] = None


class OllamaLocalModel(BaseModel):
    """A model pulled locally on this machine."""
    name: str
    size: int = 0  # bytes
    digest: str = ""
    modified_at: str = ""
    parameter_size: str = ""
    quantization_level: str = ""
    format: str = ""
    family: str = ""
    families: List[str] = Field(default_factory=list)


class OllamaRunningModel(BaseModel):
    """A model currently loaded in Ollama's memory."""
    model: str = ""
    name: str = ""
    digest: str = ""
    model_size: int = 0
    project_size: int = 0
    load_status: str = ""
    prompt_eval_count: int = 0
    prompt_eval_duration: int = 0
    eval_count: int = 0
    eval_duration: int = 0


class OllamaChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: str  # "user", "assistant", or "system"
    content: str


class VRAMEstimate(BaseModel):
    """Estimated VRAM/disk usage for a model at a given quantization."""
    model_name: str
    quantization: str  # Q4_0, Q5_K_M, Q8_0, FP16, etc.
    size_gb: float
    vram_gb: float  # how much GPU VRAM needed
    ram_gb: float  # how much system RAM needed (if offloading to CPU)
    params_billion: float  # parameter count in billions
    fits_in_vram: bool  # whether it fits in available VRAM
    fits_in_ram: bool  # whether it fits in available system RAM