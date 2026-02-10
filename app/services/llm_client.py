"""LLM Client abstraction supporting OpenAI and Anthropic."""

from typing import Optional, Literal

import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    stop_after_delay,
)

from app.config import get_settings

logger = structlog.get_logger()


class LLMClient:
    """Unified client for LLM providers (OpenAI and Anthropic)."""

    def __init__(
        self,
        provider: Optional[Literal["openai", "anthropic"]] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize LLM client.

        Args:
            provider: LLM provider ("openai" or "anthropic")
            api_key: API key (uses env var if not provided)
        """
        settings = get_settings()
        self.provider = provider or settings.llm_provider

        if self.provider == "openai":
            self.api_key = api_key or settings.openai_api_key
            self.model = settings.openai_model
            self._client = self._init_openai()
        else:
            self.api_key = api_key or settings.anthropic_api_key
            self.model = settings.anthropic_model
            self._client = self._init_anthropic()

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            logger.error("OpenAI package not installed")
            raise

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            logger.error("Anthropic package not installed")
            raise

    def _is_retryable_error(self, exception: Exception) -> bool:
        """Check if an exception should be retried.
        
        Non-retryable errors:
        - NotFoundError (model not found, resource not found)
        - AuthenticationError (invalid API key)
        - InvalidRequestError (bad request parameters)
        - PermissionDeniedError (insufficient permissions)
        - ValueError with specific messages
        
        Retryable errors:
        - RateLimitError (rate limits)
        - APIError (server errors, timeouts)
        - Connection errors
        - Timeout errors
        """
        error_type = type(exception).__name__
        error_msg = str(exception).lower()
        
        # Non-retryable error types
        non_retryable_types = [
            "NotFoundError",
            "AuthenticationError", 
            "InvalidRequestError",
            "PermissionDeniedError",
        ]
        
        # Non-retryable error messages
        non_retryable_messages = [
            "not found",
            "notfound",
            "invalid api key",
            "authentication",
            "invalid request",
            "permission denied",
            "model_not_found",
            "model not available",
            "non-retryable error",  # Our custom marker
        ]
        
        if error_type in non_retryable_types:
            return False
            
        if any(msg in error_msg for msg in non_retryable_messages):
            return False
            
        # All other errors are retryable (rate limits, server errors, timeouts, etc.)
        return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(lambda e: not isinstance(e, ValueError) or "non-retryable" not in str(e).lower()),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using the configured LLM.

        Args:
            prompt: User prompt
            system_prompt: System/context prompt
            max_tokens: Maximum tokens to generate
            temperature: Creativity/randomness (0-1)

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails after retries
        """
        logger.debug(
            "Generating with LLM",
            provider=self.provider,
            model=self.model,
            prompt_length=len(prompt),
        )

        try:
            if self.provider == "openai":
                return await self._generate_openai(
                    prompt, system_prompt, max_tokens, temperature
                )
            else:
                return await self._generate_anthropic(
                    prompt, system_prompt, max_tokens, temperature
                )
        except Exception as e:
            # Check if this is a non-retryable error
            if not self._is_retryable_error(e):
                logger.error(
                    "Non-retryable error occurred - not retrying",
                    provider=self.provider,
                    error_type=type(e).__name__,
                    error=str(e),
                )
                # Wrap in ValueError with marker to prevent retries
                raise ValueError(f"Non-retryable error: {str(e)}") from e
            
            # For retryable errors, let tenacity handle retries
            logger.warning(
                "Retryable error occurred - will retry",
                provider=self.provider,
                error_type=type(e).__name__,
                error=str(e),
            )
            raise

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using OpenAI API."""
        try:
            from openai import NotFoundError, AuthenticationError, APIError
        except ImportError:
            # Fallback if OpenAI exceptions aren't available
            NotFoundError = Exception
            AuthenticationError = Exception
            APIError = Exception

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if not response.choices or not response.choices[0].message.content:
                raise ValueError("Empty response from OpenAI API")

            return response.choices[0].message.content
        except NotFoundError as e:
            logger.error(
                "OpenAI model not found",
                model=self.model,
                error=str(e),
            )
            raise ValueError(f"Model '{self.model}' not found. Please check your model name.") from e
        except AuthenticationError as e:
            logger.error("OpenAI authentication failed", error=str(e))
            raise ValueError("Invalid API key. Please check your OPENAI_API_KEY.") from e
        except APIError as e:
            # APIError includes rate limits, server errors, etc. - these are retryable
            logger.warning("OpenAI API error", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected OpenAI error", error=str(e), error_type=type(e).__name__)
            raise

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Anthropic API."""
        try:
            from anthropic import NotFoundError, AuthenticationError, APIError
        except ImportError:
            # Fallback if Anthropic exceptions aren't available
            NotFoundError = Exception
            AuthenticationError = Exception
            APIError = Exception

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a helpful assistant.",
                messages=[{"role": "user", "content": prompt}],
            )

            if not response.content or not response.content[0].text:
                raise ValueError("Empty response from Anthropic API")

            return response.content[0].text
        except NotFoundError as e:
            logger.error(
                "Anthropic model not found",
                model=self.model,
                error=str(e),
            )
            raise ValueError(f"Model '{self.model}' not found. Please check your model name.") from e
        except AuthenticationError as e:
            logger.error("Anthropic authentication failed", error=str(e))
            raise ValueError("Invalid API key. Please check your ANTHROPIC_API_KEY.") from e
        except APIError as e:
            # APIError includes rate limits, server errors, etc. - these are retryable
            logger.warning("Anthropic API error", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected Anthropic error", error=str(e), error_type=type(e).__name__)
            raise

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.5,
    ) -> str:
        """Generate structured content (JSON, outlines, etc.).

        Uses lower temperature for more consistent output.
        """
        return await self.generate(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )


