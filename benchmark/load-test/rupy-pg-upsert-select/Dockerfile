FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy the entire rupy repository
COPY . /tmp/rupy
WORKDIR /tmp/rupy

# Build and install rupy
RUN pip install maturin && maturin build --release && pip install target/wheels/*.whl

# Setup application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY benchmark/load-test/rupy-pg-upsert-select/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY benchmark/load-test/rupy-pg-upsert-select/app.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]
