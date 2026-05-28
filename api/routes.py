from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from orchestrator.graph import run_project_analysis

router = APIRouter()


class Task(BaseModel):
    id: str
    name: str
    status: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None


class TeamMember(BaseModel):
    name: str
    role: str
    capacity_hours: Optional[int] = 8


class AnalyzeRequest(BaseModel):
    project_id: str
    project_name: str
    tasks: list[Task]
    team: list[TeamMember]
    query: Optional[str] = None


@router.post("/analyze")
def analyze_project(request: AnalyzeRequest):
    try:
        result = run_project_analysis(
            project_id=request.project_id,
            project_name=request.project_name,
            tasks=[t.model_dump() for t in request.tasks],
            team=[m.model_dump() for m in request.team],
            query=request.query,
        )
        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "plan": result.get("plan"),
            "risks": result.get("risks"),
            "allocations": result.get("allocations"),
            "status_report": result.get("status_report"),
            "progress": result.get("progress"),
            "final_decision": result.get("final_decision"),
            "errors": result.get("errors", []),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample")
def get_sample_project():
    return {
        "project_id": "proj_001",
        "project_name": "AegisPM Capstone Build",
        "tasks": [
            {"id": "T1", "name": "Design database schema", "status": "done", "assignee": "Arjun", "due_date": "2025-06-01"},
            {"id": "T2", "name": "Build LangGraph orchestrator", "status": "in_progress", "assignee": "Priya", "due_date": "2025-06-10"},
            {"id": "T3", "name": "Implement Risk Monitor agent", "status": "in_progress", "assignee": "Arjun", "due_date": "2025-06-12"},
            {"id": "T4", "name": "Build FastAPI layer", "status": "todo", "assignee": None, "due_date": "2025-06-15"},
            {"id": "T5", "name": "React dashboard UI", "status": "todo", "assignee": "Meera", "due_date": "2025-06-20"},
            {"id": "T6", "name": "Integration testing", "status": "todo", "assignee": None, "due_date": "2025-06-25"},
        ],
        "team": [
            {"name": "Arjun", "role": "Backend Engineer", "capacity_hours": 8},
            {"name": "Priya", "role": "ML Engineer", "capacity_hours": 6},
            {"name": "Meera", "role": "Frontend Engineer", "capacity_hours": 8},
        ],
        "query": "Are we on track to finish by June 25th?"
    }
class PromptRequest(BaseModel):
    prompt: str

@router.post("/parse-prompt")
def parse_prompt(request: PromptRequest):
    """
    Takes a natural language project description and converts it
    into structured project data using Groq LLM.
    """
    from utils.llm import call_llm

    system_prompt = """
You are a project data extractor. The user will describe a project in natural language.
Extract and return a JSON object with this EXACT structure:
{
  "project_name": "string",
  "tasks": [
    {"id": "T1", "name": "string", "status": "todo|in_progress|done|blocked", "assignee": "string or null", "due_date": "YYYY-MM-DD or null"}
  ],
  "team": [
    {"name": "string", "role": "string", "capacity_hours": 8}
  ],
  "query": "string - the most important question to answer about this project"
}

Rules:
- Infer task names from the description
- If deadline is like 2 weeks, calculate from today 2025-05-25
- If team size mentioned but no names, use Dev1, Dev2 etc
- Always create at least 5 tasks
- Return ONLY valid JSON, nothing else
"""

    try:
        result = call_llm(system_prompt, request.prompt)
        if result.get("parse_error"):
            raise HTTPException(status_code=500, detail="Could not parse project description")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class PromptRequest(BaseModel):
    prompt: str


@router.post("/parse-prompt")
def parse_prompt(request: PromptRequest):
    from utils.llm import call_llm

    system_prompt = """
You are a project data extractor. The user will describe a project in natural language.
Extract and return a JSON object with this EXACT structure:
{
  "project_name": "string",
  "tasks": [
    {"id": "T1", "name": "string", "status": "todo|in_progress|done|blocked", "assignee": "string or null", "due_date": "YYYY-MM-DD or null"}
  ],
  "team": [
    {"name": "string", "role": "string", "capacity_hours": 8}
  ],
  "query": "string - the most important question to answer about this project"
}

Rules:
- Infer task names from the description
- If deadline is like 2 weeks, calculate from today 2025-05-25
- If team size mentioned but no names, use Dev1, Dev2 etc
- Always create at least 5 tasks
- Return ONLY valid JSON, nothing else
"""

    try:
        result = call_llm(system_prompt, request.prompt)
        if result.get("parse_error"):
            raise HTTPException(status_code=500, detail="Could not parse project description")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    question: str
    context: str


@router.post("/chat")
def chat(request: ChatRequest):
    from utils.llm import call_llm

    system_prompt = """
You are AegisPM, an intelligent project management assistant.
You have analyzed a project and the user is asking follow-up questions.
Answer helpfully, specifically and practically in 2-4 sentences.
Return a JSON object with this structure:
{
  "answer": "your helpful answer here"
}
"""

    user_message = f"""
Project context:
{request.context}

User question: {request.question}

Answer the question based on the project context above.
"""

    try:
        result = call_llm(system_prompt, user_message)
        if result.get("parse_error"):
            return {"answer": "Sorry, I could not process that. Please try again."}
        return {"answer": result.get("answer", "No answer generated.")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))