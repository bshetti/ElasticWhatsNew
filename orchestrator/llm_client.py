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


SYSTEM_PROMPT = """\
You are a technical product writer for Elastic Observability. You will receive a single feature entry with a **Title**, **Description**, **Status**, **Source**, and context from linked GitHub PRs/issues.

Your job is to rewrite ONLY the **Title** and **Description** into polished, customer-facing copy.

## Your rewrite task

**1. A new Title** — short, benefit-oriented, scannable.
- 4-8 words maximum
- Lead with what the user can now *do* or what has *improved*, not the implementation mechanism
- Match the Elastic blog headline style: "AI-Powered Log Parsing for Streams", "One-Click Alert Muting", "Metrics Exploration in Discover"
- No version numbers, no PR numbers, no internal tracker references

**2. A new Description** — 2-4 sentences, customer-facing
- Sentence 1: What is it / what does it do? (the capability)
- Sentence 2: Why does it matter / what problem does it solve? (the value)
- Sentence 3 (optional): A concrete outcome, metric, or differentiator if available from the GitHub content
- Sentence 4 (optional): Any notable constraint, prerequisite, or "how to get started" pointer

## Tone and style rules
- Write for a technical practitioner: SRE, platform engineer, DevOps engineer
- Active voice, present tense
- No marketing superlatives ("game-changing", "powerful", "seamless", "revolutionary")
- Translate implementation language into operational outcomes:
  - "adds the math processor" -> "You can now apply math transformations directly in your processing pipeline"
  - "enforces field name spacing in wired streams" -> "Streams now validates field names and flags type mismatches before they cause silent data quality issues downstream"
- If the GitHub content reveals a specific performance number, storage saving, or latency improvement — include it
- If the GitHub content is sparse and the existing Description is the best available signal — use it, but still rewrite for customer voice
- Do NOT invent capabilities not supported by either the Description or the GitHub content

## Handling by source type

**PM Highlighted entries:** These are strategic features with richer existing descriptions.
- The existing Description is usually good — your job is to tighten, clarify, and match the style guide
- The Title rewrite is especially important here
- Check the GitHub context for any concrete metrics or outcomes not yet captured

**Release Notes entries:** These often have minimal descriptions (sometimes just the PR title repeated).
- The GitHub PR content is your primary enrichment source
- If the GitHub content is also sparse (e.g., purely a UI fix), keep the description short but still reframe it in customer language
- Minor polish/fix items can be noted with a single sentence: "Improves [area] reliability and visual consistency."

## Example

Input title: "Enforces field name spacing in wired streams and detects type mismatches in proc..."
Input description: "Enforces field name spacing in wired streams and detects type mismatches in processor configurations."

Output title: "Catch Schema Errors Before They Reach Your Data"
Output description: "Streams now validates field name formatting and detects type mismatches in processor configurations before data is written. Misconfigured processors have historically caused silent data quality issues that are difficult to trace after the fact — this surfaces them at the point of configuration so you can fix them immediately."

## Output format

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
    source: str = "Release Notes",
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
    user_parts.append(f"Source: {source}")
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
            max_tokens=1024,
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
