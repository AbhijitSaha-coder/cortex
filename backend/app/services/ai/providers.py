import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator
import httpx
from app.core.config import settings
from app.core.logging import logger


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Returns {'content': str, 'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int}"""
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Generator[str, None, None]:
        """Yields text chunks as they arrive."""
        pass


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=60.0) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return {
                "content": choice["message"]["content"],
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Generator[str, None, None]:
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        with httpx.stream("POST", url, headers=headers, json=payload, timeout=60.0) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    chunk_str = line[6:].strip()
                    if chunk_str == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(chunk_str)
                        delta = chunk_json["choices"][0]["delta"]
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                    except Exception:
                        continue


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        with httpx.Client(timeout=60.0) as client:
            res = client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            cand = data["candidates"][0]
            text = cand["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            return {
                "content": text,
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            }

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Generator[str, None, None]:
        res = self.generate(messages, system_prompt, temperature, max_tokens)
        # Yield in realistic word chunks
        words = res["content"].split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        formatted_messages = [
            {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
            for m in messages
        ]
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=60.0) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            return {
                "content": content,
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            }

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Generator[str, None, None]:
        res = self.generate(messages, system_prompt, temperature, max_tokens)
        words = res["content"].split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


class MockProvider(BaseLLMProvider):
    """
    Intelligent offline provider that synthesizes responses grounded in evidence.
    Used for tests, offline mode, and safe demo environments.
    """

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        last_message = messages[-1]["content"] if messages else ""

        # Parse evidence items if present in prompt
        import re
        evidence_matches = re.findall(r'<evidence_item index="(\d+)"[^>]*title="([^"]*)"[^>]*>(.*?)</evidence_item>', last_message, re.DOTALL)

        if evidence_matches:
            citations_found = []
            facts = []
            for idx, title, body in evidence_matches[:3]:
                citations_found.append(f"[Citation {idx}]")
                clean_snippet = body.strip().replace("\n", " ")[:150]
                facts.append(f"- According to **{title}**, {clean_snippet}... [Citation {idx}]")

            response_text = (
                f"### Research Findings\n\n"
                f"Based on the analyzed knowledge base sources, here is what was determined:\n\n"
                + "\n".join(facts) +
                f"\n\n**Synthesis:** The retrieved documents provide relevant supporting evidence for this topic. "
                f"{citations_found[0] if citations_found else ''}"
            )
        else:
            # Check if this is a general query or tool request
            response_text = (
                f"### Analysis\n\n"
                f"I reviewed your request regarding: *\"{last_message[:100]}...\"*.\n\n"
                f"No specific documents are currently indexed that directly address this question. "
                f"Please upload documents or import web pages into your Cortex library so I can provide grounded research and citations."
            )

        prompt_tokens = len(last_message.split()) + 50
        completion_tokens = len(response_text.split())

        return {
            "content": response_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Generator[str, None, None]:
        res = self.generate(messages, system_prompt, temperature, max_tokens)
        words = res["content"].split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
    if name == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    elif name == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider()
    elif name == "anthropic" and settings.ANTHROPIC_API_KEY:
        return AnthropicProvider()
    else:
        return MockProvider()

