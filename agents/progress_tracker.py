from orchestrator.state import ProjectState
from utils.llm import call_llm

SYSTEM_PROMPT = """
You are the Progress Tracking Agent inside AegisPM, an intelligent project management system.

Your job is to analyze task completion rates, detect schedule deviations,
and generate KPI metrics for the project.

Return a JSON object with this exact structure:
{
  "kpis": {
    "total_tasks": number,
    "completed": number,
    "in_progress": number,
    "todo": number,
    "blocked": number,
    "completion_percentage": number,
    "on_track": true|false
  },
  "schedule_deviation": [
    {
      "task_id": "string",
      "task_name": "string",
      "status": "string",
      "deviation": "ahead|on_time|at_risk|delayed"
    }
  ],
  "burndown": {
    "total_tasks": number,
    "remaining_tasks": number,
    "days_remaining": number,
    "required_daily_rate": number,
    "current_daily_rate": number
  },
  "summary": "1-2 sentence plain English progress summary."
}
"""


def run_progress_tracker(state: ProjectState) -> ProjectState:
    try:
        task_lines = "\n".join(
            f"- Task {t['id']}: {t['name']} | status: {t['status']} "
            f"| assignee: {t.get('assignee', 'unassigned')} | due: {t.get('due_date', 'TBD')}"
            for t in state["tasks"]
        )

        total = len(state["tasks"])
        done = sum(1 for t in state["tasks"] if t["status"] == "done")
        in_progress = sum(1 for t in state["tasks"] if t["status"] == "in_progress")
        todo = sum(1 for t in state["tasks"] if t["status"] == "todo")
        blocked = sum(1 for t in state["tasks"] if t["status"] == "blocked")

        user_message = f"""
Project: {state['project_name']}

Tasks:
{task_lines}

Quick stats:
- Total tasks: {total}
- Completed: {done}
- In Progress: {in_progress}
- Todo: {todo}
- Blocked: {blocked}
- Completion: {round((done/total)*100)}%

Analyze the progress and generate KPIs, schedule deviation, and burndown data.
"""

        result = call_llm(SYSTEM_PROMPT, user_message)

        if not result or result.get("parse_error"):
            state["errors"].append("ProgressTracker: failed to parse LLM response")
            state["progress"] = {
                "kpis": {
                    "total_tasks": total,
                    "completed": done,
                    "in_progress": in_progress,
                    "todo": todo,
                    "blocked": blocked,
                    "completion_percentage": round((done/total)*100),
                    "on_track": False
                },
                "summary": "Progress tracking unavailable — manual review needed."
            }
        else:
            state["progress"] = result

    except Exception as e:
        state["errors"].append(f"ProgressTracker: exception — {str(e)}")
        state["progress"] = {}

    return state