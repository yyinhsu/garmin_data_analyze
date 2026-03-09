"""
Agent: wraps Gemini API calls for code generation and result interpretation.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

from .prompts import (
    CODE_GENERATION_SYSTEM,
    CODE_GENERATION_USER,
    COLUMN_CATALOGUE,
    INTERPRET_SYSTEM,
    INTERPRET_USER,
    STORY_SYSTEM,
    STORY_USER,
)

# Load .env from project root (two levels up from this file)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

MODEL = "gemini-1.5-pro"


class AnalysisAgent:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY not set. Check your .env file.")
        genai.configure(api_key=key)
        self._model = genai.GenerativeModel(MODEL)

    def _call(self, prompt: str, images: list[Path] | None = None, max_tokens: int = 4096) -> str:
        parts: list = [prompt]
        if images:
            for p in images[:3]:
                if p.exists():
                    img = genai.upload_file(str(p), mime_type="image/png") if p.stat().st_size > 4_000_000 \
                          else {"mime_type": "image/png", "data": p.read_bytes()}
                    parts.append(img)

        response = self._model.generate_content(
            parts,
            generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens),
        )
        return response.text.strip()

    # ------------------------------------------------------------------ #
    # 1. Generate analysis code
    # ------------------------------------------------------------------ #

    def generate_code(self, topic: str, hypothesis: str, tree_summary: str) -> str:
        prompt = (
            CODE_GENERATION_SYSTEM + "\n\n"
            + CODE_GENERATION_USER.format(
                topic=topic,
                hypothesis=hypothesis,
                tree_summary=tree_summary,
                column_catalogue=COLUMN_CATALOGUE,
            )
        )
        code = self._call(prompt, max_tokens=4096)
        # Strip markdown fences if present
        code = re.sub(r"^```python\s*", "", code, flags=re.MULTILINE)
        code = re.sub(r"^```\s*$", "", code, flags=re.MULTILINE)
        return code.strip()

    # ------------------------------------------------------------------ #
    # 2. Interpret results → insight + decision
    # ------------------------------------------------------------------ #

    def interpret(
        self,
        topic: str,
        hypothesis: str,
        stdout: str,
        png_paths: list[Path],
        tree_summary: str,
    ) -> dict:
        prompt = (
            INTERPRET_SYSTEM + "\n\n"
            + INTERPRET_USER.format(
                topic=topic,
                hypothesis=hypothesis,
                stdout=stdout[:4000],
                tree_summary=tree_summary,
            )
        )
        raw = self._call(prompt, images=png_paths, max_tokens=1024)

        # Parse JSON
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except json.JSONDecodeError:
                    result = {}
            else:
                result = {}

        if not result:
            result = {
                "insight": raw[:300],
                "decision": "b",
                "rationale": "JSON parsing failed, defaulting to side-explore",
                "next_hypothesis": "",
            }

        for key in ("insight", "decision", "rationale", "next_hypothesis"):
            result.setdefault(key, "")

        return result

    # ------------------------------------------------------------------ #
    # 3. Final story synthesis
    # ------------------------------------------------------------------ #

    def generate_story(self, topic: str, tree_summary: str) -> str:
        prompt = (
            STORY_SYSTEM + "\n\n"
            + STORY_USER.format(topic=topic, tree_summary=tree_summary)
        )
        return self._call(prompt, max_tokens=4096)
