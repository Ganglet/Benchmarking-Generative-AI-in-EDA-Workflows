# Docker container for EDA AI Benchmarking Framework
FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies and EDA tools
RUN apt-get update && apt-get install -y \
    # Build essentials
    build-essential \
    git \
    wget \
    curl \
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

# Optional: Install Ollama (uncomment if needed)
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

