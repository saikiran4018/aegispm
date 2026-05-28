from langgraph.graph import StateGraph, END

from orchestrator.state import ProjectState
from agents.planner import run_planner
from agents.risk_monitor import run_risk_monitor
from agents.resource_allocator import run_resource_allocator
from agents.communicator import run_communicator
from agents.decision_arbiter import run_decision_arbiter
from agents.progress_tracker import run_progress_tracker
from agents.solution_engine import run_solution_engine


def build_graph() -> StateGraph:
    graph = StateGraph(ProjectState)

    graph.add_node("planner", run_planner)
    graph.add_node("risk_monitor", run_risk_monitor)
    graph.add_node("resource_allocator", run_resource_allocator)
    graph.add_node("communicator", run_communicator)
    graph.add_node("progress_tracker", run_progress_tracker)
    graph.add_node("solution_engine", run_solution_engine)
    graph.add_node("decision_arbiter", run_decision_arbiter)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "risk_monitor")
    graph.add_edge("risk_monitor", "resource_allocator")
    graph.add_edge("resource_allocator", "communicator")
    graph.add_edge("communicator", "progress_tracker")
    graph.add_edge("progress_tracker", "solution_engine")
    graph.add_edge("solution_engine", "decision_arbiter")
    graph.add_edge("decision_arbiter", END)

    return graph.compile()


aegispm_graph = build_graph()


def run_project_analysis(
    project_id: str,
    project_name: str,
    tasks: list[dict],
    team: list[dict],
    query: str | None = None,
) -> ProjectState:
    initial_state: ProjectState = {
        "project_id": project_id,
        "project_name": project_name,
        "tasks": tasks,
        "team": team,
        "query": query,
        "plan": None,
        "risks": None,
        "allocations": None,
        "status_report": None,
        "progress": None,
        "solution": None,
        "final_decision": None,
        "errors": [],
    }

    final_state = aegispm_graph.invoke(initial_state)
    return final_state