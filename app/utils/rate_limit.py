"""
Rate limiting utilities for authentication endpoints.

This module provides simple rate limiting to prevent brute-force attacks.
For production it is better to use a more robust solution like slowapi or
Redis-based rate limiting.

Usage:
  ```python
  from app.utils.rate_limit import InMemoryRateLimiter
  
  limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=60)
  
  @router.post("/login")
  async def login(request: Request, ...):
    client_ip = request.client.host
    if not limiter.is_allowed(client_ip):
      raise HTTPException(status_code=429, detail="Too many requests")
      ...
  ```
"""
from datetime import datetime, timedelta, timezone
from typing import Dict
from collections import defaultdict
import asyncio


class InMemoryRateLimiter:
  """
  Simple in-memory rate limiter.
  
  WARNING: This is not suitable for production with multiple workers/instances.
  In that case, is better to use Redis-based rate limiting or a library like slowapi.
  """
  
  def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
    """
    Initialize rate limiter.
    
    Args:
      max_attempts: Maximum number of attempts allowed in the time window
      window_seconds: Time window in seconds
    """
    self.max_attempts = max_attempts
    self.window_seconds = window_seconds
    # Store: {identifier: [(timestamp1, ), (timestamp2, ), ...]}
    self._attempts: Dict[str, list[datetime]] = defaultdict(list)
    self._lock = asyncio.Lock()
  
  async def is_allowed(self, identifier: str) -> bool:
    """
    Check if request is allowed for the given identifier.
    
    Args:
      identifier: Unique identifier (e.g., IP address, user ID)
      
    Returns:
      True if request is allowed, False if rate limit exceeded
    """
    async with self._lock:
      now = datetime.now(timezone.utc)
      window_start = now - timedelta(seconds=self.window_seconds)
      
      # Clean up old attempts
      self._attempts[identifier] = [
        attempt_time
        for attempt_time in self._attempts[identifier]
        if attempt_time > window_start
      ]
      
      # Check if limit exceeded
      if len(self._attempts[identifier]) >= self.max_attempts:
        return False
      
      # Record this attempt
      self._attempts[identifier].append(now)
      return True
  
  async def reset(self, identifier: str) -> None:
      """
      Reset rate limit for an identifier (e.g., after successful login).
      
      Args:
        identifier: Unique identifier
      """
      async with self._lock:
        if identifier in self._attempts:
          del self._attempts[identifier]
  
  async def reset_all(self) -> None:
    """Reset rate limit for all identifiers. Useful for testing."""
    async with self._lock:
      self._attempts.clear()
  
  async def get_retry_after(self, identifier: str) -> int | None:
    """
    Get seconds until the identifier can retry.
    
    Args:
      identifier: Unique identifier
      
    Returns:
      Seconds until retry is allowed, or None if allowed now
    """
    async with self._lock:
      if identifier not in self._attempts or not self._attempts[identifier]:
        return None
      
      now = datetime.now(timezone.utc)
      oldest_attempt = min(self._attempts[identifier])
      retry_time = oldest_attempt + timedelta(seconds=self.window_seconds)
      
      if retry_time <= now:
        return None
      
      return int((retry_time - now).total_seconds())


# Global rate limiter instances for different endpoints
# NOTE: In production with multiple workers, is better the Redis-based solution
login_rate_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=60)
registration_rate_limiter = InMemoryRateLimiter(max_attempts=3, window_seconds=300)


async def check_rate_limit(
  identifier: str,
  limiter: InMemoryRateLimiter
) -> tuple[bool, int | None]:
  """
  Check rate limit and return result with retry-after time.
  
  Args:
    identifier: Unique identifier (IP, user ID, etc.)
    limiter: Rate limiter instance to use
    
  Returns:
    Tuple of (is_allowed, retry_after_seconds)
  """
  is_allowed = await limiter.is_allowed(identifier)
  
  if not is_allowed:
    retry_after = await limiter.get_retry_after(identifier)
    return False, retry_after
  
  return True, None


# Example usage in route:
"""
from fastapi import Request, HTTPException, status
from app.utils.rate_limit import login_rate_limiter, check_rate_limit

@router.post("/login")
async def login_for_access_token(
  request: Request,
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: DBDep
) -> Token:
  # Rate limiting by IP address
  client_ip = request.client.host if request.client else "unknown"
  
  is_allowed, retry_after = await check_rate_limit(
    identifier=client_ip,
    limiter=login_rate_limiter
  )
  
  if not is_allowed:
    headers = {}
    if retry_after:
      headers["Retry-After"] = str(retry_after)
    
    raise HTTPException(
      status_code=status.HTTP_429_TOO_MANY_REQUESTS,
      detail=f"Too many login attempts. Try again in {retry_after} seconds.",
      headers=headers
    )
  
  # ... rest of login logic ...
  
  # On successful login, optionally reset the rate limit
  # await login_rate_limiter.reset(client_ip)
"""
