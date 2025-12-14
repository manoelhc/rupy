from fastapi import FastAPI

# Create a FastAPI application instance
app = FastAPI()

# Define a GET endpoint at the root path ("/")
@app.get("/")
async def root():
    """
    Handles GET requests to the root path and returns a simple message.
    """
    return {"message": "Hello World"}