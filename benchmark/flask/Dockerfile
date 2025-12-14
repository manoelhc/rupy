ARG PY_VERSION="3.13"
FROM python:${PY_VERSION}-slim
WORKDIR /app
COPY main.py .
RUN pip install flask
CMD ["python", "main.py"]