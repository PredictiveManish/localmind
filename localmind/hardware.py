"""Hardware detection using psutil and GPU detection for NVIDIA, AMD, Intel, and Apple Silicon."""
from __future__ import annotations
import platform
import subprocess
import psutil
from typing import List, Optional
from .models import CPUInfo, RAMInfo, GPUInfo, StorageInfo, HardwareReport
from .utils import log_warning


def get_cpu_info() -> CPUInfo:
    """Return CPU information."""
    freq = psutil.cpu_freq()
    return CPUInfo(
        name=platform.processor() or "Unknown CPU",
        physical_cores=psutil.cpu_count(logical=False) or 1,
        logical_cores=psutil.cpu_count(logical=True) or 1,
        max_frequency_mhz=freq.max if freq else 0.0,
    )


def get_ram_info() -> RAMInfo:
    """Return RAM info in GB."""
    mem = psutil.virtual_memory()
    return RAMInfo(
        total_gb=round(mem.total / (1024 ** 3), 2),
        available_gb=round(mem.available / (1024 ** 3), 2),
    )


def _detect_nvidia_gpus() -> List[GPUInfo]:
    """Detect NVIDIA GPUs using GPUtil."""
    gpus: List[GPUInfo] = []
    try:
        import GPUtil
        gpu_list = GPUtil.getGPUs()
        for gpu in gpu_list:
            gpus.append(GPUInfo(
                name=gpu.name,
                vram_mb=gpu.memoryTotal,
                driver_version=gpu.driver,
                vendor="NVIDIA",
            ))
    except ImportError:
        pass
    except Exception as e:
        log_warning(f"NVIDIA GPU detection failed: {e}")
    return gpus


def _detect_amd_gpus_windows() -> List[GPUInfo]:
    """Detect AMD GPUs on Windows using WMI."""
    gpus: List[GPUInfo] = []
    try:
        import win32com.client
        wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        service = wmi.ConnectServer(".")
        classes = service.ExecQuery("SELECT * FROM Win32_VideoController")
        for gpu in classes:
            name = str(gpu.Name or "Unknown AMD GPU")
            if "AMD" in name or "Radeon" in name or "RX" in name:
                vram = 0
                if gpu.AdapterRAM:
                    vram = int(gpu.AdapterRAM) // (1024 ** 2)
                driver_ver = str(gpu.DriverVersion or "")
                gpus.append(GPUInfo(
                    name=name,
                    vram_mb=vram,
                    driver_version=driver_ver if driver_ver else None,
                    vendor="AMD",
                ))
    except ImportError:
        pass
    except Exception as e:
        log_warning(f"AMD GPU detection (Windows WMI) failed: {e}")
    return gpus


def _detect_amd_gpus_linux() -> List[GPUInfo]:
    """Detect AMD GPUs on Linux via sysfs."""
    gpus: List[GPUInfo] = []
    try:
        import os
        amd_path = "/sys/bus/pci/devices/"
        if not os.path.exists(amd_path):
            return gpus

        for device in os.listdir(amd_path):
            vendor_file = os.path.join(amd_path, device, "vendor")
            if os.path.exists(vendor_file):
                with open(vendor_file, "r") as f:
                    vendor_id = f.read().strip()
                if vendor_id == "0x1002":  # AMD vendor ID
                    class_file = os.path.join(amd_path, device, "class")
                    if os.path.exists(class_file):
                        with open(class_file, "r") as f:
                            class_id = f.read().strip()
                        if "030000" in class_id:  # Display controller
                            name_file = os.path.join(amd_path, device, "device", "driver", "device", "name")
                            name = "AMD GPU"
                            if os.path.exists(name_file):
                                with open(name_file, "r") as f:
                                    name = f.read().strip()
                            # Try to get VRAM from memory info
                            vram = 0
                            mem_file = os.path.join(amd_path, device, "resource")
                            if os.path.exists(mem_file):
                                try:
                                    with open(mem_file, "r") as f:
                                        lines = f.readlines()
                                        if len(lines) >= 2:
                                            vram = int(lines[1].split()[2]) // (1024 ** 2)
                                except (ValueError, IndexError):
                                    pass
                            gpus.append(GPUInfo(
                                name=name,
                                vram_mb=vram if vram > 0 else 0,
                                vendor="AMD",
                            ))
    except Exception as e:
        log_warning(f"AMD GPU detection (Linux sysfs) failed: {e}")
    return gpus


def _detect_intel_gpus_windows() -> List[GPUInfo]:
    """Detect Intel integrated GPUs on Windows using WMI."""
    gpus: List[GPUInfo] = []
    try:
        import win32com.client
        wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        service = wmi.ConnectServer(".")
        classes = service.ExecQuery("SELECT * FROM Win32_VideoController")
        for gpu in classes:
            name = str(gpu.Name or "")
            if "Intel" in name or "UHD" in name or "Iris" in name:
                vram = 0
                if gpu.AdapterRAM:
                    vram = int(gpu.AdapterRAM) // (1024 ** 2)
                driver_ver = str(gpu.DriverVersion or "")
                gpus.append(GPUInfo(
                    name=name,
                    vram_mb=vram,
                    driver_version=driver_ver if driver_ver else None,
                    vendor="Intel",
                    is_unified_memory=True,  # Integrated GPUs share system RAM
                ))
    except ImportError:
        pass
    except Exception as e:
        log_warning(f"Intel GPU detection (Windows WMI) failed: {e}")
    return gpus


def _detect_intel_gpus_linux() -> List[GPUInfo]:
    """Detect Intel integrated GPUs on Linux via sysfs."""
    gpus: List[GPUInfo] = []
    try:
        import os
        amd_path = "/sys/bus/pci/devices/"
        if not os.path.exists(amd_path):
            return gpus

        for device in os.listdir(amd_path):
            vendor_file = os.path.join(amd_path, device, "vendor")
            if os.path.exists(vendor_file):
                with open(vendor_file, "r") as f:
                    vendor_id = f.read().strip()
                if vendor_id == "0x8086":  # Intel vendor ID
                    class_file = os.path.join(amd_path, device, "class")
                    if os.path.exists(class_file):
                        with open(class_file, "r") as f:
                            class_id = f.read().strip()
                        if "030000" in class_id:  # Display controller
                            name_file = os.path.join(amd_path, device, "device", "driver", "device", "name")
                            name = "Intel Integrated GPU"
                            if os.path.exists(name_file):
                                with open(name_file, "r") as f:
                                    name = f.read().strip()
                            gpus.append(GPUInfo(
                                name=name,
                                vram_mb=0,
                                vendor="Intel",
                                is_unified_memory=True,
                            ))
    except Exception as e:
        log_warning(f"Intel GPU detection (Linux sysfs) failed: {e}")
    return gpus


def _detect_apple_silicon() -> List[GPUInfo]:
    """Detect Apple Silicon GPU on macOS via system_profiler."""
    gpus: List[GPUInfo] = []
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout:
            output = result.stdout
            # Extract GPU name from output
            for line in output.splitlines():
                if "Chipset Model" in line:
                    name = line.split(":")[1].strip() if ":" in line else "Apple Silicon GPU"
                if "Total Number of Displays" in line or "Display" in line:
                    break
            else:
                name = "Apple Silicon GPU"
            
            # Get total RAM as unified memory (GPU can access all of it)
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024 ** 3)
            
            # Determine GPU memory based on Mac model
            gpu_mem = 0
            if total_gb >= 128:
                gpu_mem = 192 * 1024  # M3 Ultra
            elif total_gb >= 64:
                gpu_mem = 128 * 1024  # M2/M3 Max
            elif total_gb >= 36:
                gpu_mem = 96 * 1024   # M2/M3 Pro/Max
            elif total_gb >= 24:
                gpu_mem = 64 * 1024   # M2/M3
            elif total_gb >= 16:
                gpu_mem = 32 * 1024   # M1/M2/M3
            elif total_gb >= 8:
                gpu_mem = 16 * 1024   # M1/M2/M3 base
            else:
                gpu_mem = int(total_gb * 512)  # Shared memory estimation
            
            gpus.append(GPUInfo(
                name=name if name else "Apple Silicon GPU",
                vram_mb=gpu_mem,
                vendor="Apple",
                is_unified_memory=True,
            ))
    except FileNotFoundError:
        pass  # Not macOS
    except Exception as e:
        log_warning(f"Apple Silicon GPU detection failed: {e}")
    return gpus


def _detect_amd_gpus_via_rocm() -> List[GPUInfo]:
    """Detect AMD GPUs via rocm-smi on Linux."""
    gpus: List[GPUInfo] = []
    try:
        result = subprocess.run(
            ["rocm-smi", "--showallinfo"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            current_name = "AMD GPU"
            current_vram = 0
            for line in lines:
                if "GPU name" in line:
                    current_name = line.split(":")[1].strip() if ":" in line else "AMD GPU"
                if "VRAM" in line or "total_vram" in line.lower():
                    parts = line.split(":")
                    if len(parts) > 1:
                        try:
                            vram_str = parts[-1].strip().replace("MB", "").replace("GB", "").strip()
                            if vram_str:
                                val = float(vram_str)
                                if "GB" in line.upper():
                                    current_vram = int(val * 1024)
                                else:
                                    current_vram = int(val)
                        except ValueError:
                            pass
            if current_name and current_vram > 0:
                gpus.append(GPUInfo(
                    name=current_name,
                    vram_mb=current_vram,
                    vendor="AMD",
                ))
    except FileNotFoundError:
        pass  # rocm-smi not installed
    except Exception as e:
        log_warning(f"AMD GPU detection (rocm-smi) failed: {e}")
    return gpus


def get_gpu_info() -> List[GPUInfo]:
    """
    Return a list of GPUs, if any. Detects NVIDIA, AMD, Intel, and Apple Silicon.
    
    Detection priority:
    - macOS: Apple Silicon via system_profiler
    - Windows: GPUtil (NVIDIA), WMI (AMD/Intel)
    - Linux: GPUtil (NVIDIA), rocm-smi/sysfs (AMD), sysfs (Intel)
    """
    all_gpus: List[GPUInfo] = []
    system = platform.system()
    
    # macOS — Apple Silicon
    if system == "Darwin":
        return _detect_apple_silicon()
    
    # NVIDIA GPUs (Windows + Linux)
    nvidia_gpus = _detect_nvidia_gpus()
    if nvidia_gpus:
        all_gpus.extend(nvidia_gpus)
    
    # Windows — AMD and Intel via WMI
    if system == "Windows":
        amd_gpus = _detect_amd_gpus_windows()
        intel_gpus = _detect_intel_gpus_windows()
        all_gpus.extend(amd_gpus)
        all_gpus.extend(intel_gpus)
    
    # Linux — AMD and Intel
    elif system == "Linux":
        amd_gpus = _detect_amd_gpus_linux()
        if not amd_gpus:
            amd_gpus = _detect_amd_gpus_via_rocm()
        intel_gpus = _detect_intel_gpus_linux()
        all_gpus.extend(amd_gpus)
        all_gpus.extend(intel_gpus)
    
    return all_gpus


def get_storage_info() -> StorageInfo:
    """Return info about the root filesystem."""
    root = '\\' if platform.system() == 'Windows' else '/'
    usage = psutil.disk_usage(root)
    return StorageInfo(
        total_gb=round(usage.total / (1024 ** 3), 2),
        used_gb=round(usage.used / (1024 ** 3), 2),
        free_gb=round(usage.free / (1024 ** 3), 2),
    )


def get_full_report() -> HardwareReport:
    """Compile a complete hardware report."""
    return HardwareReport(
        os=f"{platform.system()} {platform.release()}",
        cpu=get_cpu_info(),
        ram=get_ram_info(),
        gpus=get_gpu_info(),
        storage=get_storage_info(),
    )
