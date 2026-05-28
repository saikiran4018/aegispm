from orchestrator.state import ProjectState
from utils.llm import call_llm

SYSTEM_PROMPT = """
You are the Communicator Agent inside AegisPM, an intelligent project management system.

Your job is to synthesize findings from other agents into a clean status report
that a project manager or stakeholder can read in under 2 minutes.

Return a JSON object with this exact structure:
{
  "report": {
    "headline": "One sentence project health summary",
    "status_color": "green|yellow|red",
    "key_updates": ["bullet 1", "bullet 2", "bullet 3"],
    "risks_flagged": ["risk 1", "risk 2"],
    "recommended_actions": ["action 1", "action 2"],
    "full_report": "A 3-5 sentence narrative summary of project status."
  }
}
"""


def run_communicator(state: ProjectState) -> ProjectState:
    plan_summary = state.get("plan", {}).get("summary", "No plan available.")

    risk_items = [
        r["description"] for r in (state.get("risks") or []) if "risk_id" in r
    ]
    risk_text = "\n".join(f"- {r}" for r in risk_items) or "No risks identified."

    alloc_summary = (state.get("allocations") or {}).get("summary", "No allocation changes.")

    query_context = (
        f"\nThe PM also asked: '{state['query']}' — address this in the report."
        if state.get("query")
        else ""
    )

    user_message = f"""
Project: {state['project_name']}

Plan summary: {plan_summary}

Identified risks:
{risk_text}

Resource allocation summary: {alloc_summary}
{query_context}

Write a clear status report for this project.
"""

    result = call_llm(SYSTEM_PROMPT, user_message)

    if result.get("parse_error"):
        state["errors"].append("Communicator: failed to parse LLM response")
        state["status_report"] = "Status report unavailable."
    else:
        state["status_report"] = result.get("report", {})

    return state