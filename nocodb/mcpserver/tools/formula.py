"""Formula generation tool for NocoDB MCP server.

Uses an internal LLM call (via LiteLLM) to generate NocoDB formulas
from natural language descriptions. The full formula reference is
baked into the system prompt, giving the LLM its own context window
dedicated to formula writing.
"""

import json
from typing import Optional

from fastmcp.exceptions import ToolError
from litellm import completion

from ..server import mcp
from ..dependencies import get_llm_config
from ..models import FormulaGenerateResult


SYSTEM_PROMPT_TEMPLATE = """\
You are a NocoDB formula expert. Your ONLY job is to write correct NocoDB formulas.

RULES:
- Use ONLY functions and operators from the reference below. Do NOT invent functions.
- Field references use curly braces: {{FieldName}}
- Field names are case-sensitive - use the EXACT column names provided
- String literals use single quotes inside formulas
- Return ONLY valid JSON with these keys: "formula", "explanation", "examples"
  - "formula": the complete formula string ready to paste into a NocoDB formula field
  - "explanation": a brief (1-2 sentence) description of what the formula does
  - "examples": a list of 1-3 example output values as strings
- Do NOT include any text outside the JSON object
- Do NOT wrap the JSON in markdown code blocks

FORMULA REFERENCE:
{formula_reference}
"""

USER_PROMPT_TEMPLATE = """\
Write a NocoDB formula that does the following:
{description}

Available columns: {columns}

Return ONLY valid JSON: {{"formula": "...", "explanation": "...", "examples": ["..."]}}"""


@mcp.tool
def formula_generate(
    description: str,
    columns: str,
    model: Optional[str] = None,
) -> FormulaGenerateResult:
    """Generate a NocoDB formula from a natural language description.

    Uses AI to write a formula based on the available columns and
    the NocoDB formula reference. Returns the formula for inspection
    before integration.

    Args:
        description: What the formula should do (e.g., "Calculate total price
            as quantity times unit price, with 10% discount if status is VIP")
        columns: Comma-separated column names available in the table
            (e.g., "Name,Quantity,Unit Price,Status,Created At")
        model: Optional LLM model override (default: from NOCODB_LLM_MODEL env var)

    Returns:
        FormulaGenerateResult with formula string, explanation, and examples.

    Requires NOCODB_LLM_API_KEY environment variable to be set.
    """
    llm_config = get_llm_config()
    if llm_config is None:
        raise ToolError(
            "Formula generation requires LLM configuration. "
            "Set NOCODB_LLM_API_KEY environment variable. "
            "Optionally set NOCODB_LLM_MODEL and NOCODB_LLM_API_BASE."
        )

    # Load formula reference at call time to avoid circular imports
    from ..resources import FORMULA_CONTENT

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(formula_reference=FORMULA_CONTENT)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        description=description,
        columns=columns,
    )

    use_model = model or llm_config.model

    kwargs = {
        "model": use_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 2048,
        "temperature": 0.2,
        "api_key": llm_config.api_key,
    }
    if llm_config.api_base:
        kwargs["api_base"] = llm_config.api_base

    try:
        response = completion(**kwargs)
    except Exception as e:
        raise ToolError(f"LLM call failed: {e}") from e

    # Parse response
    content = response.choices[0].message.content or ""
    json_str = content.strip()

    # Strip markdown code block wrappers if present
    if json_str.startswith("```"):
        lines = json_str.split("\n")
        json_str = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        raise ToolError(f"LLM returned invalid JSON. Raw response:\n{content}")

    formula = parsed.get("formula", "")
    explanation = parsed.get("explanation", "")
    examples = parsed.get("examples", [])

    if not formula:
        raise ToolError(f"LLM did not return a formula. Parsed response:\n{parsed}")

    return FormulaGenerateResult(
        formula=formula,
        explanation=explanation,
        examples=examples if isinstance(examples, list) else [str(examples)],
        model=use_model,
    )
