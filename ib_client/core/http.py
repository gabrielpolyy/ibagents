import ssl
import httpx
import os
import asyncio
from typing import Any, Dict, Optional
from httpx import Response
import logging

logger = logging.getLogger(__name__)

BASE = os.getenv("IB_BASE", "https://localhost:8765/v1/api")
CTX = ssl._create_unverified_context()  # ignore self-signed cert

class IBAPIError(Exception):
    """Base exception for IB API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)

async def _request_with_retry(
    method: str,
    path: str,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    **kwargs
) -> Dict[str, Any]:
    """Make HTTP request with automatic retries"""
    
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                response = await client.request(method, f"{BASE}{path}", **kwargs)
                
                # Handle different response scenarios
                if response.status_code == 401:
                    raise IBAPIError("Authentication required", status_code=401)
                elif response.status_code == 403:
                    raise IBAPIError("Access forbidden", status_code=403)
                elif response.status_code >= 500:
                    if attempt < max_retries:
                        logger.warning(f"Server error {response.status_code}, retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        continue
                    raise IBAPIError(f"Server error: {response.status_code}", status_code=response.status_code)
                
                response.raise_for_status()
                
                # Handle empty responses
                if not response.content:
                    return {}
                    
                return response.json()
                
        except httpx.RequestError as e:
            if attempt < max_retries:
                logger.warning(f"Request failed: {e}, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay * (2 ** attempt))
                continue
            raise IBAPIError(f"Request failed after {max_retries} retries: {e}")
        except Exception as e:
            if attempt < max_retries and "timeout" in str(e).lower():
                logger.warning(f"Timeout error, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay * (2 ** attempt))
                continue
            raise
    
    raise IBAPIError(f"Max retries ({max_retries}) exceeded")

async def _get(path: str, **params) -> Dict[str, Any]:
    """GET request with retry logic"""
    return await _request_with_retry("GET", path, params=params)

async def _post(path: str, json_data: Optional[Dict] = None, **params) -> Dict[str, Any]:
    """POST request with retry logic"""
    kwargs = {"params": params}
    if json_data:
        kwargs["json"] = json_data
    return await _request_with_retry("POST", path, **kwargs)

async def _delete(path: str, **params) -> Dict[str, Any]:
    """DELETE request with retry logic"""
    return await _request_with_retry("DELETE", path, params=params) 