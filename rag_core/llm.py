import logging
from typing import Any, List, Optional

import requests
from langchain_core.language_models.llms import LLM

from config import API_KEY, MODEL_NAME, MAX_TOKENS

log = logging.getLogger("studentrag.llm")


class OpenRouterLLM(LLM):

    api_key:    str = API_KEY
    model:      str = MODEL_NAME
    max_tokens: int = MAX_TOKENS

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        log.debug("Calling OpenRouter model=%s tokens=%d", self.model, self.max_tokens)
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":      self.model,
                    "max_tokens": self.max_tokens,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=90,
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("OpenRouter request timed out after 90 s.")
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(f"Network error reaching OpenRouter: {exc}") from exc

        if not response.ok:
            raise RuntimeError(
                f"OpenRouter API error {response.status_code}: {response.text}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected OpenRouter response shape: {data}") from exc
