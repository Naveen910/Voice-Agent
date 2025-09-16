from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType, ZeroShotAgent
from langchain.prompts import PromptTemplate
from tools.google_calendar import google_calendar_tool
from tools.google_sheets import google_sheets_menu_tool 
from langchain.memory import ConversationBufferMemory

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = Ollama(
    model="llama3.1:8b-instruct-q2_K",  
    base_url="http://localhost:11434"
)

# Tools for receptionist
tools = [
    google_calendar_tool,      
    google_sheets_menu_tool,   
]

# Receptionist-style system prompt
prefix = """You are an AI receptionist for a restaurant. 
You can talk to customers and you have access to the following tools:

{tool_names}

When you need to use a tool, you MUST follow this exact format (no code, no explanations):

Thought: [your reasoning here]
Action: one of {tool_names}
Action Input: the plain text input for that tool

If no tool is needed, just answer normally like a human receptionist would.
"""


suffix = """Begin!

Customer: {input}
{agent_scratchpad}"""

tool_names = ", ".join([t.name for t in tools])
prompt = ZeroShotAgent.create_prompt(
    tools,
    prefix=prefix.format(tool_names=tool_names),
    suffix=suffix,
    input_variables=["input", "agent_scratchpad"],
)



# LangChain Agent
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"prompt": prompt},
    handle_parsing_errors=True,
    memory=memory
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
        reply = result.get("output", "Sorry, I couldn’t process that request.")
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Apologies, something went wrong: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
