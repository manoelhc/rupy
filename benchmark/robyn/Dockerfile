ARG PY_VERSION="3.13"
FROM python:${PY_VERSION}-slim
WORKDIR /app
COPY main.py .
RUN apt update && \
    apt install -y git build-essential rustc -y && \
    pip install robyn && \
    apt remove -y git build-essential rustc && \
    apt autoremove -y && \
    rm -rf ~/.cache ~/.cargo && \
    rm -rf /var/lib/apt/lists/*
CMD ["python", "main.py"]
