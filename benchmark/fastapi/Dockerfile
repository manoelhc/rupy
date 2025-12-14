ARG PY_VERSION="3.13"
FROM python:${PY_VERSION}-slim
WORKDIR /app
COPY main.py .
RUN pip install fastapi uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]