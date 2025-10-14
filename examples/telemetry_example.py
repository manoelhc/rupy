#!/usr/bin/env python3
"""
Example showing OpenTelemetry integration in Rupy.

This example demonstrates how to enable telemetry and use
the various OpenTelemetry features.
"""

from rupy import Rupy, Request, Response

# Create a Rupy application
app = Rupy()

# Enable OpenTelemetry telemetry
# You can optionally specify an OTLP endpoint
app.enable_telemetry(
    # endpoint="http://localhost:4317",  # Uncomment to send to OTLP collector
    service_name="rupy-telemetry-demo"
)

# Check telemetry status
print(f"Telemetry enabled: {app.is_telemetry_enabled()}")


@app.route("/", methods=["GET"])
def index(request: Request) -> Response:
    return Response("Hello, World! Telemetry is enabled.")


@app.route("/user/<username>", methods=["GET"])
def get_user(request: Request, username: str) -> Response:
    return Response(f"User profile for: {username}")


@app.route("/api/data", methods=["POST"])
def post_data(request: Request) -> Response:
    return Response(f"Received data: {request.body}")


@app.route("/slow", methods=["GET"])
def slow_endpoint(request: Request) -> Response:
    import time

    time.sleep(0.5)  # Simulate slow operation
    return Response("This was a slow operation")


@app.route("/error", methods=["GET"])
def error_endpoint(request: Request) -> Response:
    # This will cause an internal server error in the metrics
    return Response("Error endpoint", status=500)


if __name__ == "__main__":
    print("Starting Rupy server with OpenTelemetry enabled...")
    print("Try these endpoints:")
    print("  curl http://127.0.0.1:8000/")
    print("  curl http://127.0.0.1:8000/user/alice")
    print("  curl -X POST -d 'test data' http://127.0.0.1:8000/api/data")
    print("  curl http://127.0.0.1:8000/slow")
    print("  curl http://127.0.0.1:8000/error")
    print("\nMetrics and traces will be logged to console.")
    print("To export to an OTLP collector, uncomment the endpoint parameter above.")

    app.run(host="127.0.0.1", port=8000)
