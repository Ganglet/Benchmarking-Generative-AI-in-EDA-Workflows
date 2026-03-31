# Docker container for EDA AI Benchmarking Framework
# ─────────────────────────────────────────────────────────────────────────────
# NOTE ON REPRODUCIBILITY:
#   The original experiments were conducted on macOS (Apple Silicon) using:
#     - Icarus Verilog  12.0  (Homebrew)
#     - Verilator       5.038 (Homebrew)
#     - Yosys           0.58  (Homebrew)
#   This container installs EDA tools from the Debian Trixie apt repository.
#   Tool versions may differ slightly, but the pipeline behaviour is identical.
#
# NOTE ON OLLAMA:
#   Ollama must run on the HOST machine (not inside this container).
#   The container connects to it via the OLLAMA_BASE_URL environment variable:
#     - Windows / Mac Docker Desktop : http://host.docker.internal:11434 (default)
#     - Linux                        : http://<host-ip>:11434
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch apt sources to HTTPS (HTTP port 80 is blocked in some environments)
# python:3.11-slim ships with ca-certificates so HTTPS verification works.
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org|https://security.debian.org|g' /etc/apt/sources.list.d/debian.sources

# Install EDA tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    iverilog \
    verilator \
    yosys \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt /tmp/requirements.txt

# Install torch CPU-only first (all LLM inference goes through Ollama on the
# host; HuggingFace/torch is a fallback not exercised when Ollama is available)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create workspace directory
WORKDIR /workspace

# Copy project files
COPY Quantitative/ /workspace/Quantitative/
COPY requirements.txt /workspace/

# Set environment variables
ENV PYTHONPATH=/workspace
ENV PATH="/workspace/Quantitative:${PATH}"

# Verify installations and print exact versions (shown at build time)
RUN echo "=== Tool versions in this container ===" && \
    python3 --version && \
    pip --version && \
    iverilog -V 2>&1 | head -n 1 && \
    verilator --version 2>&1 | head -n 1 && \
    yosys -V 2>&1 | head -n 1 && \
    echo "========================================" && \
    echo "Original experiments used (macOS/Homebrew):" && \
    echo "  Icarus Verilog 12.0 | Verilator 5.038 | Yosys 0.58"

# Create directories for outputs
RUN mkdir -p /workspace/results /workspace/figures

# Default command
CMD ["/bin/bash"]
