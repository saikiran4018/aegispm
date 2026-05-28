from typing import TypedDict, Optional


class ProjectState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────
    project_id: str
    project_name: str
    tasks: list[dict]
    team: list[dict]
    query: Optional[str]

    # ── Agent outputs (filled in as agents run) ────────────────────────────
    plan: Optional[dict]
    risks: Optional[list[dict]]
    allocations: Optional[dict]
    status_report: Optional[str]
    final_decision: Optional[dict]
    progress: Optional[dict]

    # ── Metadata ───────────────────────────────────────────────────────────
    errors: list[str]