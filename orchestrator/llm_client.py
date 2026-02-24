"""
LLM client for enhancing feature descriptions using litellm.

Uses litellm.completion() for provider flexibility.
Config via env vars:
  - LLM_MODEL: model identifier (default: anthropic/claude-haiku-4-5-20251001)
  - Provider API keys: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, etc.
"""

import json
import os

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


def get_model() -> str:
    """Read LLM_MODEL env var, with default."""
    return os.environ.get("LLM_MODEL", "anthropic/claude-haiku-4-5-20251001")


def is_llm_available() -> bool:
    """Check if litellm is installed and an API key is present."""
    if not LITELLM_AVAILABLE:
        return False

    # Check for common provider API keys
    key_vars = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "AZURE_API_KEY",
        "COHERE_API_KEY",
    ]
    return any(os.environ.get(k) for k in key_vars)


SYSTEM_PROMPT = """You are a technical writer for the Elastic Observability "What's New" page.

Your job is to rewrite feature titles and descriptions so they are:
- Clear and benefit-focused for end users (developers, SREs, platform engineers)
- 2-3 sentences for the description, highlighting what the user can now do and why it matters
- Free of internal PR references, issue numbers, or implementation details
- Professional but approachable in tone
- Accurate to the technical content provided

You will be given the current title and description, along with context from linked PRs and documentation pages.

Return your response as a JSON object with exactly two keys:
{"title": "...", "description": "..."}

Do NOT include any other text outside the JSON object."""


def enhance_feature(
    title: str,
    description: str,
    pr_bodies: list[str],
    doc_summaries: list[str],
    section_name: str,
    status: str,
) -> dict:
    """
    Enhance a feature's title and description using an LLM.

    Returns: {"title": str, "description": str, "error": str|None}
    """
    if not LITELLM_AVAILABLE:
        return {"title": title, "description": description, "error": "litellm not installed"}

    if not is_llm_available():
        return {"title": title, "description": description, "error": "No API key configured"}

    # Build the user prompt with context
    user_parts = []
    user_parts.append(f"Section: {section_name}")
    user_parts.append(f"Status: {status}")
    user_parts.append(f"\nCurrent title: {title}")
    user_parts.append(f"Current description: {description}")

    if pr_bodies:
        user_parts.append("\n--- Context from linked PRs/Issues ---")
        for i, body in enumerate(pr_bodies, 1):
            # Truncate each PR body to 3000 chars
            truncated = body[:3000]
            if len(body) > 3000:
                truncated += "... [truncated]"
            user_parts.append(f"\nPR {i}:\n{truncated}")

    if doc_summaries:
        user_parts.append("\n--- Context from documentation pages ---")
        for i, doc in enumerate(doc_summaries, 1):
            # Truncate doc text to 5000 chars
            truncated = doc[:5000]
            if len(doc) > 5000:
                truncated += "... [truncated]"
            user_parts.append(f"\nDoc {i}:\n{truncated}")

    user_message = "\n".join(user_parts)

    try:
        response = litellm.completion(
            model=get_model(),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=500,
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON from response, handling possible markdown code blocks
        if content.startswith("```"):
            # Strip markdown code fences
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()

        result = json.loads(content)

        if "title" not in result or "description" not in result:
            return {
                "title": title,
                "description": description,
                "error": "LLM response missing title or description fields",
            }

        return {
            "title": result["title"],
            "description": result["description"],
            "error": None,
        }

    except json.JSONDecodeError:
        return {
            "title": title,
            "description": description,
            "error": "LLM returned invalid JSON",
        }
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            error_msg = "Rate limited — please wait and try again"
        return {
            "title": title,
            "description": description,
            "error": error_msg,
        }
