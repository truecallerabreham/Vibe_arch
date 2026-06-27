import asyncio
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.services.extraction_pipeline import ExtractionPipeline

router = APIRouter(prefix="/api", tags=["extraction"])

tasks: dict[str, dict] = {}

class ExtractRequest(BaseModel):
    repo_url: str = Field(min_length=1)

class ExtractResponse(BaseModel):
    task_id: str

@router.post("/extract", response_model=ExtractResponse)
async def start_extraction(request: ExtractRequest):
    """Start architecture extraction for a repo URL."""
    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {"status": "queued", "result": None, "progress": []}

    asyncio.create_task(_run_extraction(task_id, request.repo_url))

    return ExtractResponse(task_id=task_id)

@router.get("/extract/stream/{task_id}")
async def stream_extraction(task_id: str):
    """SSE stream of extraction progress."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        while True:
            task = tasks.get(task_id)
            if not task:
                break

            if task["status"] == "error":
                yield f"data: ERROR: {task['error']}\n\n"
                break

            if task["progress"]:
                while task["progress"]:
                    msg = task["progress"].pop(0)
                    yield f"data: {msg}\n\n"

            if task["status"] == "complete":
                break

            await asyncio.sleep(0.1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/architecture/{task_id}")
async def get_architecture(task_id: str):
    """Get completed architecture result."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "complete":
        raise HTTPException(status_code=202, detail="Extraction still in progress")
    return {"architecture": task["result"].model_dump()}

async def _run_extraction(task_id: str, repo_url: str):
    """Run extraction pipeline in background."""
    try:
        tasks[task_id]["status"] = "running"

        async def progress(msg: str):
            tasks[task_id]["progress"].append(msg)

        pipeline = ExtractionPipeline()
        architecture = await pipeline.run(repo_url, progress_callback=progress)

        tasks[task_id]["result"] = architecture
        tasks[task_id]["status"] = "complete"
        tasks[task_id]["progress"].append("Done!")
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["progress"].append(f"ERROR: {str(e)}")
