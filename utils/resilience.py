"""Resilience utilities: retry logic and circuit breaker for RAG service.

Provides graceful degradation when V2 (LangGraph) fails, falling back to V1.
Circuit breaker prevents cascading failures by temporarily blocking requests
to a failing service.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected."""

    pass


@dataclass
class CircuitBreakerState:
    """
    State machine for circuit breaker pattern.

    States:
    - closed: Normal operation, requests allowed
    - open: Too many failures, requests blocked
    - half-open: Testing if service recovered, one request allowed
    """

    failures: int = 0
    successes_in_half_open: int = 0
    last_failure: Optional[datetime] = None
    state: str = "closed"  # closed, open, half-open
    threshold: int = 5  # Failures before opening
    reset_timeout: int = 60  # Seconds before trying half-open
    half_open_success_threshold: int = 2  # Successes to close from half-open

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure = datetime.now()
        self.successes_in_half_open = 0

        if self.state == "half-open":
            # Failed during test, reopen
            self.state = "open"
            logger.warning("Circuit breaker REOPENED after half-open failure")
        elif self.failures >= self.threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker OPENED after {self.failures} consecutive failures"
            )

    def record_success(self) -> None:
        """Record a success and potentially close the circuit."""
        if self.state == "half-open":
            self.successes_in_half_open += 1
            if self.successes_in_half_open >= self.half_open_success_threshold:
                self.state = "closed"
                self.failures = 0
                self.successes_in_half_open = 0
                logger.info("Circuit breaker CLOSED after successful recovery")
        elif self.state == "closed":
            # Reset failure count on success
            self.failures = 0

    def should_allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if reset timeout has passed
            if self.last_failure and datetime.now() - self.last_failure > timedelta(
                seconds=self.reset_timeout
            ):
                self.state = "half-open"
                logger.info(
                    "Circuit breaker HALF-OPEN, allowing test request"
                )
                return True
            return False

        # half-open: allow requests for testing
        return True

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "state": self.state,
            "failures": self.failures,
            "threshold": self.threshold,
            "last_failure": (
                self.last_failure.isoformat() if self.last_failure else None
            ),
            "reset_timeout_seconds": self.reset_timeout,
        }


# Global circuit breakers keyed by name
_circuit_breakers: dict[str, CircuitBreakerState] = {}


def get_circuit_breaker(
    name: str, threshold: int = 5, reset_timeout: int = 60
) -> CircuitBreakerState:
    """
    Get or create a circuit breaker for a service.

    Args:
        name: Unique identifier for the circuit (e.g., "v2_langgraph")
        threshold: Number of failures before opening
        reset_timeout: Seconds before attempting half-open

    Returns:
        CircuitBreakerState instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreakerState(
            threshold=threshold, reset_timeout=reset_timeout
        )
        logger.info(f"Created circuit breaker '{name}' (threshold={threshold})")
    return _circuit_breakers[name]


def reset_circuit_breaker(name: str) -> bool:
    """Manually reset a circuit breaker to closed state."""
    if name in _circuit_breakers:
        cb = _circuit_breakers[name]
        cb.state = "closed"
        cb.failures = 0
        cb.successes_in_half_open = 0
        logger.info(f"Circuit breaker '{name}' manually reset")
        return True
    return False


def get_all_circuit_breaker_status() -> dict:
    """Get status of all circuit breakers."""
    return {name: cb.get_status() for name, cb in _circuit_breakers.items()}


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for retry logic using tenacity.

    Args:
        max_attempts: Maximum retry attempts
        min_wait: Minimum wait between retries (seconds)
        max_wait: Maximum wait between retries (seconds)
        exceptions: Exception types to retry on

    Usage:
        @with_retry(max_attempts=3)
        def call_external_service():
            ...
    """

    def decorator(func: Callable):
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )(func)

    return decorator


def with_circuit_breaker(
    circuit_name: str,
    threshold: int = 5,
    reset_timeout: int = 60,
):
    """
    Decorator for circuit breaker pattern.

    Args:
        circuit_name: Unique name for this circuit
        threshold: Failures before opening
        reset_timeout: Seconds before half-open test

    Usage:
        @with_circuit_breaker("v2_langgraph")
        def invoke_langgraph(query: str) -> dict:
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            circuit = get_circuit_breaker(circuit_name, threshold, reset_timeout)

            if not circuit.should_allow_request():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{circuit_name}' is open"
                )

            try:
                result = func(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception as e:
                circuit.record_failure()
                raise

        return wrapper

    return decorator


def with_retry_and_circuit_breaker(
    circuit_name: str,
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    threshold: int = 5,
    reset_timeout: int = 60,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Combined decorator for retry logic with circuit breaker.

    Retries happen within the circuit breaker - if all retries fail,
    it counts as one failure for the circuit breaker.

    Args:
        circuit_name: Unique name for this circuit
        max_attempts: Maximum retry attempts per call
        min_wait: Minimum wait between retries
        max_wait: Maximum wait between retries
        threshold: Failures before opening circuit
        reset_timeout: Seconds before half-open test
        exceptions: Exception types to retry on

    Usage:
        @with_retry_and_circuit_breaker("v2_langgraph", max_attempts=3)
        def invoke_langgraph(query: str) -> dict:
            ...
    """

    def decorator(func: Callable):
        # Apply retry first (inner), then circuit breaker (outer)
        retry_decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            circuit = get_circuit_breaker(circuit_name, threshold, reset_timeout)

            if not circuit.should_allow_request():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{circuit_name}' is open"
                )

            try:
                # Apply retry logic
                retried_func = retry_decorator(func)
                result = retried_func(*args, **kwargs)
                circuit.record_success()
                return result
            except RetryError as e:
                # All retries exhausted
                circuit.record_failure()
                logger.error(
                    f"All {max_attempts} retries failed for '{circuit_name}'"
                )
                raise e.last_attempt.exception() from e
            except CircuitBreakerOpenError:
                raise
            except Exception as e:
                circuit.record_failure()
                raise

        return wrapper

    return decorator
