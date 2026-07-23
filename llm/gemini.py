"""Gemini LLM Provider adapter integrating Google Generative AI API."""

import os
import logging
from typing import Dict, List, Optional
from llm.base import BaseLLMProvider, LLMResponse
from agent_runtime.budget import MODEL_RATES

logger = logging.getLogger("llm.gemini")


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider adapter."""

    name = "gemini"
    default_model = "gemini-2.0-flash"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        """Generates completion via Gemini API with fallback calculation if SDK unavailable."""
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY found, returning fallback mock response")
            from llm.mock import MockLLMProvider

            return await MockLLMProvider(
                canned_response="Fallback response: GEMINI_API_KEY missing"
            ).generate(messages)

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.default_model,
                system_instruction=system_instruction,
            )

            # Format conversation history
            contents = []
            for msg in messages:
                role = "user" if msg.get("role") in ("user", "human") else "model"
                contents.append({"role": role, "parts": [msg.get("content", "")]})

            res = await model.generate_content_async(
                contents,
                generation_config={"temperature": temperature},
            )

            text = res.text if hasattr(res, "text") else str(res)
            prompt_tokens = (
                getattr(res.usage_metadata, "prompt_token_count", 100)
                if hasattr(res, "usage_metadata")
                else 100
            )
            completion_tokens = (
                getattr(res.usage_metadata, "candidates_token_count", 50)
                if hasattr(res, "usage_metadata")
                else 50
            )

            rates = MODEL_RATES.get(self.default_model, MODEL_RATES["default"])
            cost = (prompt_tokens / 1000.0) * rates["input"] + (
                completion_tokens / 1000.0
            ) * rates["output"]

            return LLMResponse(
                content=text,
                model_name=self.default_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=round(cost, 6),
                finish_reason="stop",
            )
        except Exception as err:
            logger.error(f"Gemini API generation failed: {err}")
            from llm.mock import MockLLMProvider

            return await MockLLMProvider(
                canned_response=f"Fallback response after error: {err}"
            ).generate(messages)
