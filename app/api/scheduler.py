"""
Scheduler endpoints for periodic tasks triggered by Cloud Scheduler.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Dict

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/hello-world")
async def scheduled_hello_world(request: Request) -> Dict[str, str]:
    """
    Test endpoint for Cloud Scheduler integration.

    This endpoint can be invoked by Google Cloud Scheduler every 30 minutes.
    Later, replace this with actual scheduled tasks.

    Cloud Scheduler will send a POST request with headers and optionally a body.
    """
    # Log the request for debugging
    logger.info("Scheduled hello-world endpoint invoked")
    logger.info(f"Request headers: {request.headers}")

    # Get client info (Cloud Scheduler user agent)
    user_agent = request.headers.get("user-agent", "")

    # Optional: Verify the request is from Cloud Scheduler
    # You can check for specific headers like X-CloudScheduler
    is_cloud_scheduler = "Google-Cloud-Scheduler" in user_agent

    current_time = datetime.utcnow().isoformat()

    response = {
        "message": "Hello World from scheduled task!",
        "timestamp": current_time,
        "triggered_by": "Cloud Scheduler" if is_cloud_scheduler else "Unknown",
        "status": "success",
    }

    logger.info(f"Response: {response}")

    return response


@router.get("/hello-world")
async def scheduled_hello_world_get() -> Dict[str, str]:
    """
    GET version of the hello world endpoint for manual testing.
    """
    current_time = datetime.utcnow().isoformat()

    return {
        "message": "Hello World! This is the GET version for manual testing.",
        "timestamp": current_time,
        "note": "Cloud Scheduler will use POST method",
        "status": "success",
    }
