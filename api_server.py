import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from browser_use import Agent
from browser_use.llm.openai.chat import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Browser-use API Wrapper")

class TaskRequest(BaseModel):
    task: str
    model: str = "gpt-4o"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run_task")
async def run_task(request: TaskRequest):
    try:
        # Initialize LLM
        llm = ChatOpenAI(model=request.model)
        
        # Initialize Agent
        agent = Agent(
            task=request.task,
            llm=llm
        )
        
        # Run Agent
        history = await agent.run()
        
        # Return final result
        return {
            "task": request.task,
            "status": "completed",
            "final_result": history.final_result(),
            "steps": len(history.history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
