from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType, ZeroShotAgent
from tools.google_calendar import google_calendar_tool
from tools.google_sheets import google_sheets_menu_tool
from langchain.memory import ConversationBufferMemory
import base64
from speech import generate_tts_audio, generate_lipsync_cues

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
llm = Ollama(
    model="llama3.1:8b-instruct-q2_K",
    base_url="http://localhost:11434"
)

# --- Tools ---
tools = [
    google_calendar_tool,
    google_sheets_menu_tool,
]

tool_names = ", ".join([t.name for t in tools])

# --- Agent Prompt ---
prefix = f"""
Think before you respond.
You are Glenda(if they ask your name tell them as Glenda), an autonomous, intelligent restaurant AI assistant.
You can use the following tools: {tool_names}.

Your job:
1. Understand any customer query in natural language.
2. Decide which tool(s) to use and in what order.
3. Execute tool actions autonomously and get results.
4. Respond naturally to the customer, incorporating tool results.

Instructions:
- Reservation Calendar: book tables. Must include party size, date/time, customer name, phone number.
- Google Sheets Menu: check menu items, just tell the items names only.
- Always provide reasoning in 'Thought' before calling a tool.
- Never ask unnecessary questions. Use best guesses if info is missing.
- Return a human-friendly response after using tools.

Tool call format:
Thought: [your reasoning]
Action: [tool name]
Action Input: [full natural language input for the tool]
"""

suffix = """
Begin!

Customer: {input}
{agent_scratchpad}
"""

prompt = ZeroShotAgent.create_prompt(
    tools,
    prefix=prefix,
    suffix=suffix,
    input_variables=["input", "agent_scratchpad"],
)

# Memory to keep track of conversation
memory = ConversationBufferMemory(memory_key="history", return_messages=True)

# Initialize agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"prompt": prompt},
    handle_parsing_errors=True,
    memory=memory
)

# --- Request Model ---
class ChatRequest(BaseModel):
    message: str

# --- Chat Endpoint ---
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Agent reasoning + tool execution
        result = agent.invoke({"input": request.message})
        reply_text = result.get("output", "Sorry, I couldn’t process that request.")

        # TTS audio
        mp3_bytes, wav_bytes = generate_tts_audio(reply_text)
        audio_base64 = base64.b64encode(mp3_bytes).decode("utf-8")

        # Lip sync
        lipsync = generate_lipsync_cues(reply_text, wav_bytes)

        messages = [
            {
                "text": reply_text,
                "audio": audio_base64,
                "lipsync": {"mouthCues": lipsync},
                "facialExpression": "smile",
                "animation": "Talking_1"
            }
        ]

        return JSONResponse(content={"messages": messages})

    except Exception as e:
        messages = [
            {
                "text": f"Error: {str(e)}",
                "audio": "",
                "lipsync": {"mouthCues": []},
                "facialExpression": "smile",
                "animation": "Talking_1"
            }
        ]
        return JSONResponse(content={"messages": messages})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
