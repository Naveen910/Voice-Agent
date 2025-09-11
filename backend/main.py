from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType

# Define API
app = FastAPI()

# Connect to Ollama
llm = Ollama(
    model="deepseek-r1:1.5b", 
    base_url="http://localhost:11434"
)

# Example Tool (you’ll add more: Gmail, Calendar, DB, File Search)
def search_files(query: str) -> str:
    # Replace with actual file search logic
    return f"Searching local files for: {query}"

tools = [
    Tool(
        name="File Search",
        func=search_files,
        description="Useful for searching local documents."
    )
]

# Initialize LangChain Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Request/Response Schema
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        reply = agent.run(request.message)
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
