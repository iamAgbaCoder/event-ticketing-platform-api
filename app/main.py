from contextlib import asynccontextmanager
from datetime import datetime
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

import colorama

colorama.just_fix_windows_console()

# Add the current directory to the path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from api.v1 import events, tickets, users
from config import get_settings
from utils.logger import setup_logger

settings = get_settings()

# Set up logger - Fix: use __name__ as the logger name and logging.INFO as the level
log_level = logging.DEBUG if settings.debug else logging.INFO
logger = setup_logger(__name__, log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Event Ticketing API...")

    try:
        # Initialize Database
        logger.info(f"Initializing database connection")
        # await initialize_database()

        logger.info("Event Ticketing API started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Event Ticketing API")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Event Ticketing REST API with automatic ticket expiration and geospatial queries",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(events.router, prefix="/api/v1")
# app.include_router(tickets.router, prefix="/api/v1")
# app.include_router(users.router, prefix="/api/v1")


# Add request logging middleware
@app.middleware("http")
async def log_request(request: Request, call_next):
    start_time = time.time()

    # Generate a unique request ID
    request_id = datetime.now().strftime("%Y%m%d%H%M%S-") + os.urandom(4).hex()

    # Set the request ID on the request object for later access
    request.state.request_id = request_id

    # Log request details
    logger.info(f"Request {request_id} started: {request.method} {request.url.path}")

    try:
        # Process the request
        response = await call_next(request)

        # Calculate and log processing time
        process_time = time.time() - start_time
        logger.info(
            f"Request {request_id} completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s"
        )

        # Add the request ID to the response headers
        response.headers["X-Request-ID"] = request_id

        return response
    except Exception as e:
        # Log the exception
        process_time = time.time() - start_time
        logger.error(
            f"Request {request_id} failed: {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.4f}s"
        )
        raise


@app.get("/")
async def root():
    return {"message": "Event Ticketing API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
