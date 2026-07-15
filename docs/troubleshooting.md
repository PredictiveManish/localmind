# Troubleshooting

Common issues, error messages, and how to fix them.

## "command not found: lm" or "lm is not recognized"

**Cause:** pip installed LocalMind to a directory not in your PATH.

**Fix:**

```bash
# Try the full Python module path instead
python -m localmind hardware

# If that works, find where pip installed it:
python -m pip show localmind

# Look for "Location:" in the output. Add that directory to your PATH.
```

**On Windows:** pip usually installs to `C:\Users\<you>\AppData\Local\Programs\Python\Python312\Scripts\`. Add this to your PATH.

**On macOS/Linux:** pip usually installs to `~/.local/bin/` or `/usr/local/bin/`. Make sure this is in your PATH.

## "GPUtil not installed" warning

**Cause:** GPUtil (the NVIDIA GPU detection library) isn't installed.

**Fix:**

- **On NVIDIA machines:** `pip install GPUtil`
- **On non-NVIDIA machines** (Mac, AMD, Intel): **Ignore this.** LocalMind uses other detection methods on these platforms. GPUtil is only needed for NVIDIA.

## "No GPU detected" on a machine that has one

This can happen with several GPU types:

### AMD GPU on Linux

**Cause:** ROCm drivers or sysfs access isn't available.

**Fix:**
```bash
# Check if ROCm is installed
rocm-smi --showinfo

# If not installed, install ROCm drivers for your distro
# Ubuntu/Debian:
sudo apt install rocm-dev rocminfo

# Then restart your terminal and run lm hardware again
```

### Intel Integrated GPU on Linux

**Cause:** sysfs path isn't accessible or drivers aren't loaded.

**Fix:**
```bash
# Check if the GPU is visible in sysfs
ls /sys/bus/pci/devices/ | head

# Check if Intel vendor ID (0x8086) is present
grep -r "0x8086" /sys/bus/pci/devices/*/vendor 2>/dev/null

# If nothing shows up, your kernel may not have Intel GPU drivers loaded
# Try: sudo modprobe i915  (for Intel graphics)
```

### NVIDIA GPU on Linux

**Cause:** NVIDIA drivers or NVML library isn't available.

**Fix:**
```bash
# Check if NVIDIA driver is loaded
nvidia-smi

# If "command not found", install NVIDIA drivers:
# Ubuntu:
sudo ubuntu-drivers autoinstall

# Then: pip install GPUtil
```

### Apple Silicon

**Cause:** Should never happen on macOS. `system_profiler` is always available.

**Fix:**
```bash
# Verify system_profiler works:
system_profiler SPDisplaysDataType

# If it works but LocalMind doesn't detect the GPU, run:
lm doctor
# Check the warnings section for any detection errors.
```

## "Ollama installation failed"

**Cause:** The automatic Ollama installer couldn't complete.

**Common causes and fixes:**

1. **No admin/sudo rights** — You need administrator privileges to install Ollama.
   - **Windows:** Run your terminal as "Run as administrator"
   - **macOS/Linux:** Prefix with `sudo` or use an admin account

2. **Firewall/antivirus blocking** — Some security software blocks `curl` or `irm` commands.
   - Temporarily disable your firewall/antivirus and try again
   - Or install Ollama manually from [ollama.com](https://ollama.com)

3. **Slow or blocked internet** — The installer downloads from `ollama.com`.
   - Check your internet connection
   - Try running the installer command manually:
     - **Windows:** `powershell -ExecutionPolicy Bypass -Command "irm https://ollama.com/install.ps1 | iex"`
     - **macOS/Linux:** `curl -fsSL https://ollama.com/install.sh | sh`

4. **Unsupported platform** — LocalMind only supports Windows, macOS, and Linux.
   - If you're on Windows Subsystem for Linux (WSL), install Ollama in WSL directly: `curl -fsSL https://ollama.com/install.sh | sh`

## "No models found" when searching

**Cause:** The Ollama API search returned no results, or the API is unreachable.

**Fix:**

```bash
# Check your internet connection
curl -I https://ollama.com

# Try a simpler search term
lm search llama
lm search mistral

# If the API is down, wait and try again
# The Ollama library API is public and may occasionally be unavailable
```

## "Could not retrieve model info"

**Cause:** `lm info` requires Ollama installed AND the model already pulled.

**Fix:**

```bash
# First, make sure Ollama is installed
ollama --version

# Then, pull the model
lm download llama3:8b

# Now try info again
lm info llama3:8b
```

## "Unknown task" when using recommend

**Cause:** You passed an invalid task name.

**Fix:** Only three tasks are supported:

```bash
lm recommend coding      # ✅
lm recommend writing     # ✅
lm recommend reasoning   # ✅
lm recommend gaming      # ❌ Not supported
```

## Models run very slowly on CPU

**Cause:** CPU inference is inherently slow. A 7B model on CPU might run at 1-3 tokens/second.

**What you can do:**

1. **Use a smaller model** — 1B-4B models run much faster on CPU
   ```bash
   lm recommend          # Check what size fits your machine
   lm download phi3:mini # Small model, fast on CPU
   ```

2. **Use a quantized model** — Quantized models use less memory and can load faster
   ```bash
   lm download llama3:8b-q4_0  # Q4 quantization
   ```

3. **Close other applications** — Free up RAM for the model

4. **Add swap space** (Linux/macOS) — If you're running out of RAM, swap can prevent crashes (but will be slower)
   ```bash
   # Linux: create a 4GB swap file
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

## Low disk space warnings

**Cause:** You have less than 10GB free disk space.

**Fix:**

```bash
# Check disk usage
lm hardware

# Free up space:
# - Delete old models you don't need: ollama rm <model>
# - Clear browser cache, downloads folder, etc.
# - Move large files to an external drive
```

## Model downloads fail or hang

**Cause:** Large models (70B+) can be 40GB+. Network issues or disk space problems can cause failures.

**Fix:**

```bash
# Check available disk space first
lm hardware

# Try downloading a smaller model first to test
lm download llama3:8b

# If the download hangs, interrupt it (Ctrl+C) and try again
# Ollama supports resuming interrupted downloads

# For very large models, consider using a wired connection instead of WiFi
```

## Multiple GPUs detected but only one is used

**Cause:** Ollama may not utilize all GPUs simultaneously on all platforms.

**What's happening:**
- LocalMind correctly detects and reports all GPUs
- Ollama's multi-GPU support depends on the platform and Ollama version
- On Linux with NVIDIA, Ollama can use multiple GPUs
- On Windows, multi-GPU support is limited
- On macOS, only the Apple Silicon GPU is available

**Workaround:** There isn't one yet. This is an Ollama limitation, not a LocalMind issue. LocalMind correctly reports all your GPUs — how Ollama uses them is up to Ollama.

## Classification seems wrong

**Cause:** The tier thresholds are based on RAM and VRAM only. They don't account for:
- CPU generation (a modern i3 beats an old i7)
- Disk speed (NVMe vs HDD)
- Available RAM (vs total RAM)
- Number of open applications

**What to do:**
- If your machine is classified as a lower tier than expected, it may have slow components (HDD, old CPU)
- If your machine is classified as a higher tier than expected, check if available RAM is much lower than total RAM
- The classification is a heuristic, not a benchmark. Use it as a starting point, not a guarantee.

## How to get help

1. Run `lm doctor` and share the full output
2. Run `lm hardware` and share the full output
3. Check your Python version: `python --version` (must be 3.11+)
4. Check your OS: `uname -a` (Linux/macOS) or `systeminfo` (Windows)

If you found a bug that isn't covered here, report it at [github.com/predictivemanish/localmind/issues](https://github.com/predictivemanish/localmind/issues).
