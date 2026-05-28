from orchestrator.state import ProjectState
from utils.llm import call_llm

SYSTEM_PROMPT = """
You are the Resource Allocator Agent inside AegisPM, an intelligent project management system.

Your job is to balance workload across the team. Look at who is assigned what,
and whether capacity is being used efficiently.

Return a JSON object with this exact structure:
{
  "allocations": [
    {
      "task_id": "string",
      "current_assignee": "string or null",
      "suggested_assignee": "string",
      "reason": "string — why this assignment makes sense"
    }
  ],
  "overloaded_members": ["name", ...],
  "underutilized_members": ["name", ...],
  "summary": "1-2 sentence plain English summary."
}
"""


def run_resource_allocator(state: ProjectState) -> ProjectState:
    task_lines = "\n".join(
        f"- Task {t['id']}: {t['name']} | assignee: {t.get('assignee', 'unassigned')} "
        f"| status: {t['status']}"
        for t in state["tasks"]
    )

    team_lines = "\n".join(
        f"- {m['name']} ({m['role']}, capacity: {m.get('capacity_hours', 8)}h/day)"
        for m in state["team"]
    )

    risk_summary = ""
    for r in (state.get("risks") or []):
        if "summary" in r and "risk_id" not in r:
            risk_summary = r.get("summary", "")
            break

    user_message = f"""
Project: {state['project_name']}

Tasks and current assignments:
{task_lines}

Team capacity:
{team_lines}

Known risks: {risk_summary}

Suggest optimal task assignments to balance the workload.
"""

    result = call_llm(SYSTEM_PROMPT, user_message)

    if result.get("parse_error"):
        state["errors"].append("ResourceAllocator: failed to parse LLM response")
        state["allocations"] = {}
    else:
        state["allocations"] = result

    return state