# Docker container for EDA AI Benchmarking Framework
FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_ROOT_USER_ACTION=ignore

# Install system dependencies and EDA tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    git \
    wget \
    curl \
    ca-certificates \
    # Python
    python3.10 \
    python3-pip \
    python3-dev \
    # EDA Tools
    iverilog \
    verilator \
    yosys \
    gtkwave \
    # Utilities
    vim \
    nano \
    less \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Note: Ollama installation and configuration
# ===========================================
# Ollama should typically be installed on the HOST machine, not in the container.
# This is recommended for GPU access and better performance.
#
# To connect from inside the container to Ollama on the host:
# - Windows/Mac Docker Desktop: Set environment variable OLLAMA_BASE_URL=http://host.docker.internal:11434
# - Linux: Use your host IP address or set OLLAMA_BASE_URL=http://<host-ip>:11434
#
# Alternative: Install Ollama inside container (not recommended for GPU use):
# RUN curl -fsSL https://ollama.com/install.sh | sh

# Create workspace directory
WORKDIR /workspace

# Copy project files
COPY Quantitative/ /workspace/Quantitative/
COPY requirements.txt /workspace/

# Set environment variables
ENV PYTHONPATH=/workspace:$PYTHONPATH
ENV PATH=/workspace/Quantitative:$PATH

# Verify installations
RUN echo "Verifying installations..." && \
    python --version && \
    pip --version && \
    iverilog -v 2>&1 | head -n 1 && \
    verilator --version 2>&1 | head -n 1 && \
    yosys -V 2>&1 | head -n 1

# Create directories for outputs
RUN mkdir -p /workspace/results /workspace/figures

# Default command
CMD ["/bin/bash"]

