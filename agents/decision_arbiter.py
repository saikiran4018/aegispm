from orchestrator.state import ProjectState
from utils.llm import call_llm

SYSTEM_PROMPT = """
You are the Decision Arbiter Agent inside AegisPM, an intelligent project management system.

You receive summaries from all other agents and must produce a final, prioritized action plan.

Classify each action by autonomy level:
  - "auto": safe to execute automatically
  - "confirm": needs PM approval
  - "escalate": requires full human review

You MUST always return a valid JSON object with this exact structure, no exceptions:
{
  "final_actions": [
    {
      "action_id": "A1",
      "description": "what should be done",
      "autonomy_level": "auto|confirm|escalate",
      "urgency": "immediate|this_week|backlog",
      "rationale": "why this action matters"
    }
  ],
  "top_priority": "The single most important thing to do right now.",
  "confidence": 0.85
}
"""


def run_decision_arbiter(state: ProjectState) -> ProjectState:
    try:
        plan_summary = (state.get("plan") or {}).get("summary", "N/A")
        alloc_summary = (state.get("allocations") or {}).get("summary", "N/A")

        risk_items = [
            f"[{r.get('severity','?').upper()}] {r['description']} (prob: {r.get('probability',0):.0%})"
            for r in (state.get("risks") or [])
            if "risk_id" in r
        ]
        risk_text = "\n".join(risk_items) or "No risks."

        report = state.get("status_report") or {}
        report_headline = report.get("headline", "N/A") if isinstance(report, dict) else str(report)

        user_message = f"""
Project: {state['project_name']}

Planner summary: {plan_summary}

Risks:
{risk_text}

Resource summary: {alloc_summary}

Overall status: {report_headline}

Produce the final prioritized action plan now. Return only JSON.
"""

        result = call_llm(SYSTEM_PROMPT, user_message)

        if not result or result.get("parse_error"):
            state["final_decision"] = {
                "final_actions": [
                    {
                        "action_id": "A1",
                        "description": "Review project manually due to parsing error",
                        "autonomy_level": "escalate",
                        "urgency": "immediate",
                        "rationale": "Agent could not parse response"
                    }
                ],
                "top_priority": "Manual review required",
                "confidence": 0.0
            }
            state["errors"].append("DecisionArbiter: parse error — fallback used")
        else:
            state["final_decision"] = result

    except Exception as e:
        state["errors"].append(f"DecisionArbiter: exception — {str(e)}")
        state["final_decision"] = {
            "final_actions": [],
            "top_priority": "Error occurred — manual review needed",
            "confidence": 0.0
        }

    return state