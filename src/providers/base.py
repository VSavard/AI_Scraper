from typing import Generator, Protocol, runtime_checkable

@runtime_checkable
class AIProvider(Protocol):
    """
    Common interface for AI language model providers.

    Any class implementing these three methods can be used as a drop-in
    provider throughout the scraper, regardless of the underlying SDK.
    """

    def complete(self, system: str, user: str, max_token: int = 1024) -> str:
        """
        Send a text prompt and return the model's full response.

        Args:
            system: System-level instruction for the model.
            user: User message content.
            max_tokens: Maximum number of tokens to generate.

        Returns:
            The model's response as a plain string.

        Raises:
            AIProviderError: If the API call fails.
        """
        ...
