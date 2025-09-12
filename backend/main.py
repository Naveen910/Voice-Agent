from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType, ZeroShotAgent
from langchain.prompts import PromptTemplate
from tools.google_calendar import google_calendar_tool

app = FastAPI()

# Connect to Ollama
llm = Ollama(
    model="llama3.1:8b-instruct-q2_K",  
    base_url="http://localhost:11434"
)

# Add tools
tools = [
    google_calendar_tool,
]

# Custom prompt for tool usage
prefix = """You are an AI voice assistant with access to the following tools:

{tools}

When you decide to use a tool, you MUST follow this format exactly:

Thought: [your reasoning]
Action: the exact tool name from the list above (do not use brackets or quotes)
Action Input: plain text input for the tool

If no tool is needed, just respond with the final answer.
"""

suffix = """Begin!

Question: {input}
{agent_scratchpad}"""


prompt = ZeroShotAgent.create_prompt(
    tools,
    prefix=prefix,
    suffix=suffix,
    input_variables=["input", "agent_scratchpad"],
)

# LangChain Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"prompt": prompt},
)

# Request/Response schema
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = agent.invoke({"input": request.message})
        reply = result["output"]

        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
