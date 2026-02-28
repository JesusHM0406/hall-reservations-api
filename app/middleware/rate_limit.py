"""
Global rate limiting middleware.

Applies rate limiting to all endpoints to prevent abuse and ensure
fair resource usage across all users.
"""
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.rate_limit import global_rate_limiter


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
  """
  Middleware to apply global rate limiting to all requests.
  
  Endpoints with specific rate limiters (login, registration) handle
  their own rate limiting, so they still respect their stricter limits.
  This middleware acts as a safety net for all other endpoints.
  """
  
  # Endpoints that have their own specific rate limiters
  # These will be checked by the middleware but won't skip it
  SPECIFIC_RATE_LIMITED_ENDPOINTS = {
    "/auth/login",
    "/users/",  # POST method only (registration)
  }
  
  def __init__(self, app: ASGIApp):
    super().__init__(app)
  
  async def dispatch(self, request: Request, call_next: Any) -> Response:
    """
    Process each request and apply rate limiting before passing to endpoint.
    
    Args:
      request: The incoming request
      call_next: The next middleware or endpoint handler
      
    Returns:
      Response from the endpoint or rate limit error
    """
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    
    # Check global rate limit
    is_allowed = await global_rate_limiter.is_allowed(client_ip)
    
    if not is_allowed:
      # Get retry-after time
      retry_after = await global_rate_limiter.get_retry_after(client_ip)
      
      headers: dict[str, str] = {}
      if retry_after:
        headers["Retry-After"] = str(retry_after)
      
      return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
          "detail": f"Too many requests. Please try again after {retry_after} seconds."
        },
        headers=headers
      )
    
    # Continue to the endpoint
    response: Response = await call_next(request)
    return response
