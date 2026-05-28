from orchestrator.state import ProjectState
from utils.llm import call_llm

SYSTEM_PROMPT = """
You are the Planner Agent inside AegisPM, an intelligent project management system.

Your job is to analyze a list of project tasks and produce a sprint plan.

Return a JSON object with this exact structure:
{
  "sprint_plan": [
    {
      "task_id": "string",
      "task_name": "string",
      "priority": "high|medium|low",
      "estimated_days": number,
      "depends_on": ["task_id", ...],
      "suggested_assignee": "string"
    }
  ],
  "summary": "A 1-2 sentence plain English summary of the plan."
}
"""


def run_planner(state: ProjectState) -> ProjectState:
    task_lines = "\n".join(
        f"- Task {t['id']}: {t['name']} | status: {t['status']} "
        f"| assignee: {t.get('assignee', 'unassigned')} | due: {t.get('due_date', 'TBD')}"
        for t in state["tasks"]
    )

    team_lines = "\n".join(
        f"- {m['name']} ({m['role']}, {m.get('capacity_hours', 8)}h/day)"
        for m in state["team"]
    )

    user_message = f"""
Project: {state['project_name']}

Tasks:
{task_lines}

Team:
{team_lines}

Please produce a prioritized sprint plan for these tasks.
"""

    result = call_llm(SYSTEM_PROMPT, user_message)

    if result.get("parse_error"):
        state["errors"].append("Planner: failed to parse LLM response")
        state["plan"] = {}
    else:
        state["plan"] = result

    return state