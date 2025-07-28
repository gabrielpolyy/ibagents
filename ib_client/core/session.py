import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .http import _get, _post, IBAPIError

logger = logging.getLogger(__name__)

class SessionAdapter:
    """
    Mixin class that provides session management functionality.
    All other adapters should inherit from this to ensure proper authentication.
    """
    
    def __init__(self):
        self._session_status: Optional[Dict] = None
        self._last_auth_check: Optional[float] = None
        self._auth_check_interval = 300  # 5 minutes
        self._keep_alive_task: Optional[asyncio.Task] = None
        self._keep_alive_interval = 60  # 1 minute
        self._session_lock = asyncio.Lock()
    
    async def _ensure_live(self) -> None:
        """
        Ensure the session is authenticated and active.
        This should be called before any API operation.
        """
        async with self._session_lock:
            current_time = time.time()
            
            # Check if we need to verify authentication status
            if (self._last_auth_check is None or 
                current_time - self._last_auth_check > self._auth_check_interval):
                
                await self._check_auth_status()
                self._last_auth_check = current_time
    
    async def _check_auth_status(self) -> Dict[str, Any]:
        """Check current authentication status"""
        try:
            status = await _post("/iserver/auth/status")
            self._session_status = status
            
            if not status.get("authenticated", False):
                logger.warning("Session not authenticated")
                raise IBAPIError("Session not authenticated. Please log in through the IB Gateway.")
            
            # Start keep-alive if not already running
            if self._keep_alive_task is None or self._keep_alive_task.done():
                self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
            
            logger.debug(f"Auth status: {status}")
            return status
            
        except IBAPIError as e:
            if e.status_code == 401:
                # Try to reauthenticate
                logger.info("Attempting to reauthenticate...")
                await self._reauthenticate()
                return await self._check_auth_status()
            raise
    
    async def _reauthenticate(self) -> None:
        """Attempt to reauthenticate the session"""
        try:
            result = await _post("/iserver/reauthenticate")
            logger.info(f"Reauthentication result: {result}")
        except Exception as e:
            logger.error(f"Reauthentication failed: {e}")
            raise IBAPIError("Reauthentication failed. Manual login may be required.")
    
    async def _tickle(self) -> None:
        """Send keep-alive ping to maintain session"""
        try:
            await _post("/tickle")
            logger.debug("Keep-alive tickle sent")
        except Exception as e:
            logger.warning(f"Keep-alive tickle failed: {e}")
    
    async def _keep_alive_loop(self) -> None:
        """Background task to maintain session with periodic tickles"""
        while True:
            try:
                await asyncio.sleep(self._keep_alive_interval)
                await self._tickle()
            except asyncio.CancelledError:
                logger.info("Keep-alive loop cancelled")
                break
            except Exception as e:
                logger.error(f"Keep-alive loop error: {e}")
                # Continue the loop despite errors
    
    async def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        await self._ensure_live()
        return self._session_status or {}
    
    async def logout(self) -> None:
        """Logout and cleanup session"""
        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass
        
        try:
            await _post("/logout")
            logger.info("Session logged out")
        except Exception as e:
            logger.warning(f"Logout failed: {e}")
        
        self._session_status = None
        self._last_auth_check = None
    
    def __del__(self):
        """Cleanup when adapter is destroyed"""
        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel() 