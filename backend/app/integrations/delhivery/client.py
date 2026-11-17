import logging
import re
import time
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def redact_sensitive(text: str) -> str:
    """Masks authorization tokens and API keys in logs and error strings."""
    if not text:
        return ""
    # Redact common key patterns
    redacted = re.sub(r'(Bearer\s+)[A-Za-z0-9_\-\.]{8,}', r'\1[REDACTED]', text, flags=re.IGNORECASE)
    redacted = re.sub(r'(key=)[A-Za-z0-9_\-\.]{8,}', r'\1[REDACTED]', redacted, flags=re.IGNORECASE)
    redacted = re.sub(r'(x-api-key["\']?\s*:\s*["\']?)[A-Za-z0-9_\-\.]{8,}', r'\1[REDACTED]', redacted, flags=re.IGNORECASE)
    return redacted


class DelhiveryError(Exception):
    """Base exception for Delhivery Maps integration."""
    pass


class DelhiveryAuthError(DelhiveryError):
    """Raised on 401 Unauthorized or 403 Forbidden."""
    pass


class DelhiveryRateLimitError(DelhiveryError):
    """Raised on 429 Too Many Requests."""
    pass


class DelhiveryClient:
    """
    HTTPX-based client for Delhivery Maps & Location Intelligence Platform APIs.
    Features:
    - Retries with exponential backoff on transient errors (500, 502, 503, 504, 429).
    - Request timeout configuration.
    - Automatic credential injection and credential redaction in logs.
    - Structured error reporting.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or settings.DELHIVERY_API_KEY
        self.base_url = (base_url or settings.DELHIVERY_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.DELHIVERY_REQUEST_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.DELHIVERY_MAX_RETRIES
        self.is_configured = bool(self.api_key and self.api_key.strip())

        if not self.is_configured:
            logger.info("DelhiveryClient initialized WITHOUT active API key. Operating in graceful fallback mode.")
        else:
            masked_key = self.api_key[:4] + "..." + self.api_key[-3:] if len(self.api_key) > 7 else "***"
            logger.info(f"DelhiveryClient initialized with key [{masked_key}] for base URL: {self.base_url}")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "EmergencyRouteAI/1.0.0",
        }
        if self.is_configured and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["x-api-key"] = self.api_key
        return headers

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes an HTTP request to Delhivery API with retries and structured error handling.
        """
        if not self.is_configured:
            raise DelhiveryAuthError("Delhivery API key is not configured.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        backoff = settings.DELHIVERY_RETRY_BACKOFF_SECONDS

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                    )

                if response.status_code in (401, 403):
                    msg = f"Delhivery authentication failed with status {response.status_code}: {response.text}"
                    logger.error(redact_sensitive(msg))
                    raise DelhiveryAuthError(redact_sensitive(msg))

                if response.status_code == 429:
                    msg = f"Delhivery rate limit reached (status 429). Attempt {attempt}/{self.max_retries}"
                    logger.warning(msg)
                    if attempt == self.max_retries:
                        raise DelhiveryRateLimitError("Delhivery rate limit exceeded.")
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                if response.status_code >= 500:
                    msg = f"Delhivery server error (status {response.status_code}). Attempt {attempt}/{self.max_retries}"
                    logger.warning(msg)
                    if attempt == self.max_retries:
                        raise DelhiveryError(f"Delhivery server error: {response.status_code} {response.text}")
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                response.raise_for_status()
                return response.json()

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                logger.warning(f"Delhivery connection error ({type(exc).__name__}). Attempt {attempt}/{self.max_retries}")
                if attempt == self.max_retries:
                    raise DelhiveryError(f"Delhivery request timed out after {self.max_retries} attempts.") from exc
                time.sleep(backoff)
                backoff *= 2
            except DelhiveryError:
                raise
            except Exception as e:
                msg = f"Unexpected error while calling Delhivery API: {str(e)}"
                logger.error(redact_sensitive(msg))
                raise DelhiveryError(redact_sensitive(msg)) from e

        raise DelhiveryError("Maximum retries exhausted without response.")

