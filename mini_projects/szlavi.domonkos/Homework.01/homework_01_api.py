"""
FastAPI application that calls worldtimeapi.org to get Budapest's current time in UTC.

This application demonstrates:
- FastAPI framework usage
- HTTP requests to external APIs (httpx)
- Error handling
- Pydantic models for response validation

Requirements:
- Python 3.11+
- fastapi
- httpx
- uvicorn (for running the server)

Installation:
    pip install fastapi httpx uvicorn

Running the application:
    uvicorn homework_01_api:app --reload

API Endpoint:
    GET /api/budapest-time
    
Example usage:
    curl http://localhost:8000/api/budapest-time
    
    Response:
    {
        "timezone": "Europe/Budapest",
        "datetime": "2024-12-23T15:30:45.123456+01:00",
        "utc_datetime": "2024-12-23T14:30:45.123456Z",
        "utc_offset": "+01:00"
    }
"""

from datetime import datetime
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Initialize FastAPI application
app = FastAPI(
    title="Budapest Time API",
    description="Get current date and time for Budapest timezone in UTC format",
    version="1.0.0"
)

# Pydantic model for response
class TimeResponse(BaseModel):
    """Response model for time data."""
    timezone: str
    datetime: str
    utc_datetime: str
    utc_offset: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: Optional[str] = None


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with information about the API."""
    return {
        "message": "Budapest Time API",
        "version": "1.0.0",
        "endpoints": {
            "budapest_time": "/api/budapest-time",
            "health": "/health"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/budapest-time", response_model=TimeResponse, tags=["Time"])
async def get_budapest_time():
    """
    Get current date and time for Budapest in UTC format.
    
    Calls the worldtimeapi.org API to fetch the current time for Europe/Budapest timezone.
    
    Returns:
        TimeResponse: Contains timezone, local datetime, UTC datetime, and UTC offset
        
    Raises:
        HTTPException: If the API call fails or data is invalid
    """
    try:
        # Make HTTP request to worldtimeapi.org
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://worldtimeapi.org/api/timezone/Europe/Budapest",
                timeout=10.0
            )
            response.raise_for_status()  # Raise exception for bad status codes
            
        data = response.json()
        
        # Parse the datetime from API response
        local_datetime = data.get("datetime", "")
        utc_offset = data.get("utc_offset", "")
        timezone = data.get("timezone", "Europe/Budapest")
        
        # Parse the datetime string and convert to UTC
        # The datetime from API is in ISO format: "2024-12-23T15:30:45.123456+01:00"
        dt = datetime.fromisoformat(local_datetime)
        
        # Convert to UTC and format
        utc_dt = dt.astimezone().__class__.utcnow()
        # More reliable: use the UTC datetime directly from the API
        utc_datetime = data.get("utc_datetime", "")
        if not utc_datetime:
            # Fallback: manually calculate if not provided
            utc_datetime = dt.astimezone().isoformat().replace("+00:00", "Z")
        
        return TimeResponse(
            timezone=timezone,
            datetime=local_datetime,
            utc_datetime=utc_datetime,
            utc_offset=utc_offset
        )
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to worldtimeapi.org timed out"
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch time data: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse datetime: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@app.get("/api/budapest-time/raw", tags=["Time"])
async def get_budapest_time_raw():
    """
    Get raw response from worldtimeapi.org for Budapest timezone.
    
    Returns:
        dict: Raw API response with all available fields
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://worldtimeapi.org/api/timezone/Europe/Budapest",
                timeout=10.0
            )
            response.raise_for_status()
            
        return response.json()
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to worldtimeapi.org timed out"
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch time data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )