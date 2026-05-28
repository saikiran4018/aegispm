from orchestrator.state import ProjectState
from utils.llm import call_llm

SYSTEM_PROMPT = """
You are the Solution Engine Agent inside AegisPM, an intelligent project management system.

You receive a full project analysis including risks, resource issues, and blocked tasks.
Your job is to ACTIVELY FIX all the problems found — not just report them.

You must produce a resolved version of the project with:
1. Reassigned tasks (fix unassigned and overloaded members)
2. Unblocked tasks (provide specific action steps)
3. Updated timeline (fix at-risk deadlines)
4. Auto-executed vs confirmed actions

Return a JSON object with this EXACT structure:
{
  "resolved_tasks": [
    {
      "task_name": "string - real descriptive name",
      "original_assignee": "string or null",
      "new_assignee": "string",
      "original_status": "string",
      "new_status": "string",
      "original_due_date": "string or null",
      "new_due_date": "string or null",
      "action_taken": "string - what exactly was done to fix this",
      "action_type": "auto|confirm|escalate"
    }
  ],
  "unblocked_tasks": [
    {
      "task_name": "string",
      "blocker": "string - what was blocking it",
      "solution": "string - specific steps to unblock",
      "assigned_to": "string",
      "estimated_resolution": "string - e.g. 2 days"
    }
  ],
  "timeline_changes": [
    {
      "task_name": "string",
      "original_deadline": "string",
      "new_deadline": "string",
      "reason": "string"
    }
  ],
  "team_rebalancing": [
    {
      "member": "string",
      "original_tasks": ["task name", ...],
      "new_tasks": ["task name", ...],
      "status": "overloaded|balanced|underutilized"
    }
  ],
  "overall_resolution": {
    "problems_found": number,
    "problems_fixed": number,
    "auto_executed": number,
    "needs_confirmation": number,
    "new_completion_date": "string",
    "confidence": 0.0_to_1.0
  },
  "summary": "2-3 sentence plain English summary of what was fixed and the new project outlook"
}
"""


def run_solution_engine(state: ProjectState) -> ProjectState:
    try:
        # Build context from all previous agents
        task_lines = "\n".join(
            f"- {t['name']} | status: {t['status']} "
            f"| assignee: {t.get('assignee', 'unassigned')} | due: {t.get('due_date', 'TBD')}"
            for t in state["tasks"]
        )

        team_lines = "\n".join(
            f"- {m['name']} ({m['role']}, {m.get('capacity_hours', 8)}h/day)"
            for m in state["team"]
        )

        risk_items = [
            f"[{r.get('severity','?').upper()}] {r['description']} — mitigation: {r.get('mitigation','')}"
            for r in (state.get("risks") or [])
            if "risk_id" in r
        ]
        risk_text = "\n".join(risk_items) or "No risks."

        alloc_issues = []
        alloc = state.get("allocations") or {}
        if alloc.get("overloaded_members"):
            alloc_issues.append(f"Overloaded: {', '.join(alloc['overloaded_members'])}")
        if alloc.get("underutilized_members"):
            alloc_issues.append(f"Underutilized: {', '.join(alloc['underutilized_members'])}")

        blocked = [t['name'] for t in state["tasks"] if t['status'] == 'blocked']
        unassigned = [t['name'] for t in state["tasks"] if not t.get('assignee')]

        user_message = f"""
Project: {state['project_name']}

Current Tasks:
{task_lines}

Team:
{team_lines}

Identified Risks:
{risk_text}

Resource Issues:
{chr(10).join(alloc_issues) or 'None'}

Blocked Tasks: {', '.join(blocked) or 'None'}
Unassigned Tasks: {', '.join(unassigned) or 'None'}

Status Report: {(state.get('status_report') or {}).get('headline', 'N/A')}

Now ACTIVELY FIX all these problems. Reassign tasks, unblock blockers, 
adjust timelines, and rebalance the team. Use the real task names, not T1/T2/T3.
Produce a complete resolution plan.
"""

        result = call_llm(SYSTEM_PROMPT, user_message)

        if not result or result.get("parse_error"):
            state["errors"].append("SolutionEngine: failed to parse LLM response")
            state["solution"] = {}
        else:
            state["solution"] = result

    except Exception as e:
        state["errors"].append(f"SolutionEngine: exception — {str(e)}")
        state["solution"] = {}

    return state