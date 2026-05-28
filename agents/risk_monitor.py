from orchestrator.state import ProjectState
from utils.llm import call_llm

SYSTEM_PROMPT = """
You are the Risk Monitor Agent inside AegisPM, an intelligent project management system.

Your job is to proactively identify risks in a project based on task statuses,
deadlines, team workload, and dependencies.

Return a JSON object with this exact structure:
{
  "risks": [
    {
      "risk_id": "R1",
      "description": "string — what could go wrong",
      "probability": 0.0_to_1.0,
      "severity": "low|medium|high|critical",
      "affected_tasks": ["task_id", ...],
      "mitigation": "string — what to do about it"
    }
  ],
  "overall_health": "green|yellow|red",
  "summary": "1-2 sentence plain English risk summary."
}
"""


def run_risk_monitor(state: ProjectState) -> ProjectState:
    task_lines = "\n".join(
        f"- Task {t['id']}: {t['name']} | status: {t['status']} | due: {t.get('due_date', 'TBD')}"
        for t in state["tasks"]
    )

    plan_summary = state.get("plan", {}).get("summary", "No plan generated yet.")

    user_message = f"""
Project: {state['project_name']}

Tasks:
{task_lines}

Planner's assessment:
{plan_summary}

Identify all risks in this project. Be specific and practical.
"""

    result = call_llm(SYSTEM_PROMPT, user_message)

    if result.get("parse_error"):
        state["errors"].append("RiskMonitor: failed to parse LLM response")
        state["risks"] = []
    else:
        state["risks"] = result.get("risks", [])
        state["risks"].append({
            "overall_health": result.get("overall_health", "yellow"),
            "summary": result.get("summary", ""),
        })

    return state