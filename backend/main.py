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

When you decide to use a tool, you MUST output exactly this format:

Thought: [reasoning]
Action: one of {tool_names} (write only the tool name, nothing else)
Action Input: plain text input for that tool

Do not invent new actions. If no tool is needed, just reply normally.
"""

suffix = """Begin!

Question: {input}
{agent_scratchpad}"""


tool_names = ", ".join([t.name for t in tools])
prompt = ZeroShotAgent.create_prompt(
    tools,
    prefix=prefix.format(tool_names=tool_names, tools="{tools}"),
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
    handle_parsing_errors=True,
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
        reply = result.get("output", str(result))
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
