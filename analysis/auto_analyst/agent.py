"""
Agent: wraps Gemini API calls for code generation and result interpretation.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .prompts import (
    CODE_GENERATION_SYSTEM,
    CODE_GENERATION_USER,
    COLUMN_CATALOGUE,
    INTERPRET_SYSTEM,
    INTERPRET_USER,
    STORY_SYSTEM,
    STORY_USER,
)

# Load .env from project root
load_dotenv(Path(__file__).parent.parent.parent / ".env")

MODEL = "gemini-2.5-flash"


class AnalysisAgent:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY not set. Check your .env file.")
        self.client = genai.Client(api_key=key)

    def _call(self, prompt: str, images: list[Path] | None = None, max_tokens: int = 4096) -> str:
        parts: list = [prompt]
        if images:
            for p in images[:3]:
                if p.exists():
                    parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type="image/png"))

        for attempt in range(4):
            try:
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=parts,
                    config=types.GenerateContentConfig(max_output_tokens=max_tokens),
                )
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) and attempt < 3:
                    wait = 60 * (attempt + 1)
                    print(f"  [rate limit] waiting {wait}s before retry {attempt + 2}/4 ...", flush=True)
                    import time; time.sleep(wait)
                else:
                    raise

    # ------------------------------------------------------------------ #
    # 1. Generate analysis code
    # ------------------------------------------------------------------ #

    def generate_code(self, topic: str, hypothesis: str, tree_summary: str) -> str:
        prompt = (
            CODE_GENERATION_SYSTEM
            + "\n\n"
            + CODE_GENERATION_USER.format(
                topic=topic,
                hypothesis=hypothesis,
                tree_summary=tree_summary,
                column_catalogue=COLUMN_CATALOGUE,
            )
        )
        code = self._extract_code(self._call(prompt, max_tokens=8192))

        # Syntax-check with up to 2 fix attempts
        for attempt in range(2):
            try:
                compile(code, "<generated>", "exec")
                break  # valid
            except SyntaxError as e:
                if attempt == 1:
                    break  # give up, let executor catch it
                fix_prompt = (
                    f"The Python code below has a SyntaxError: {e}\n\n"
                    f"Return ONLY the corrected Python code, no markdown fences, no explanation.\n\n{code}"
                )
                code = self._extract_code(self._call(fix_prompt, max_tokens=4096))

        return code

    @staticmethod
    def _extract_code(raw: str) -> str:
        """Concatenate ALL Python code blocks from a markdown response."""
        # Find all ```python ... ``` blocks and join them
        blocks = re.findall(r"```python\s*\n(.*?)```", raw, re.DOTALL)
        if blocks:
            return "\n\n".join(b.strip() for b in blocks)
        # Fallback: strip any ``` fences line by line
        code = re.sub(r"^```(?:python)?\s*$", "", raw.strip(), flags=re.MULTILINE)
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
        prompt = INTERPRET_SYSTEM + "\n\n" + INTERPRET_USER.format(
            topic=topic,
            hypothesis=hypothesis,
            stdout=stdout[:4000],
            tree_summary=tree_summary,
        )
        raw = self._call(prompt, images=png_paths, max_tokens=1024)

        def _sanitize_json(text: str) -> str:
            """Replace literal newlines inside JSON string values using a state machine."""
            result = []
            in_string = False
            escape = False
            for char in text:
                if escape:
                    result.append(char)
                    escape = False
                elif char == "\\" and in_string:
                    result.append(char)
                    escape = True
                elif char == '"':
                    in_string = not in_string
                    result.append(char)
                elif char == "\n" and in_string:
                    result.append(" ")
                else:
                    result.append(char)
            return "".join(result)

        def _try_parse(text: str) -> dict | None:
            """Try json.loads; on failure sanitize literal newlines in string values."""
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
            try:
                return json.loads(_sanitize_json(text))
            except json.JSONDecodeError:
                return None

        # Strategy 1: find the outer JSON object (strip fences first)
        clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
        clean = re.sub(r"```\s*$", "", clean.strip(), flags=re.MULTILINE).strip()
        json_match = re.search(r"\{[\s\S]*\}", clean)
        result = _try_parse(json_match.group()) if json_match else None

        # Strategy 2: regex-extract individual fields (fallback)
        if result is None:
            def _extract_field(field: str) -> str:
                m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', raw, re.DOTALL)
                if m:
                    return m.group(1).replace("\n", " ")
                return ""
            decision_m = re.search(r'"decision"\s*:\s*"([abcd])"', raw)
            result = {
                "insight": _extract_field("insight") or raw[:300],
                "decision": decision_m.group(1) if decision_m else "b",
                "rationale": _extract_field("rationale") or "field-level extraction",
                "next_hypothesis": _extract_field("next_hypothesis"),
            }

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
        prompt = STORY_SYSTEM + "\n\n" + STORY_USER.format(
            topic=topic, tree_summary=tree_summary
        )
        return self._call(prompt, max_tokens=4096)
