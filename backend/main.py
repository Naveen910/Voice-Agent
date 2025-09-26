from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType, ZeroShotAgent
from langchain.prompts import PromptTemplate
from tools.google_calendar import google_calendar_tool
from tools.google_sheets import google_sheets_menu_tool
from langchain.memory import ConversationBufferMemory
import base64


from tts import generate_tts_audio, generate_lipsync_cues

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = Ollama(
    model="gemma3:4b",
    base_url="http://localhost:11434"
)

# Tools for receptionist
tools = [
    google_calendar_tool,
    google_sheets_menu_tool,
]

# Receptionist-style system prompt
prefix = """You are Glenda, a friendly and efficient virtual receptionist for a restaurant. 
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
memory = ConversationBufferMemory(memory_key="history", return_messages=True)
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"prompt": prompt},
    handle_parsing_errors=True,
    memory=memory
)

# Request schema
class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 1️⃣ Get assistant reply text
        result = agent.invoke({"input": request.message})
        reply_text = result.get("output", "Sorry, I couldn’t process that request.")

        # 2️⃣ Generate TTS audio (bytes)
        audio_bytes = generate_tts_audio(reply_text)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        # 3️⃣ Generate lip sync cues
        lipsync = generate_lipsync_cues(reply_text, audio_bytes)

        # 4️⃣ Response format for Avatar.jsx
        message = {
            "audio": audio_base64,   # base64 mp3
            "lipsync": {"mouthCues": lipsync},
            "animation": "Talking",
            "facialExpression": "default",
            "text": reply_text
        }

        return JSONResponse(content={"message": message})

    except Exception as e:
        return JSONResponse(
            content={
                "message": {
                    "audio": "",
                    "lipsync": {"mouthCues": []},
                    "animation": "Idle",
                    "facialExpression": "default",
                    "text": f"Error: {str(e)}"
                }
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
