from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentType
from tools.google_calendar import google_calendar_tool
from tools.google_sheets import google_sheets_menu_tool
from langchain.memory import ConversationBufferMemory
import base64
from speech import generate_tts_audio, generate_lipsync_cues

# ----------------------------
# FastAPI Setup
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# LLM Setup
# ----------------------------
llm = Ollama(
    model="llama3.2:3b",
    base_url="http://192.168.1.4:11434"
)

# ----------------------------
# Tools
# ----------------------------
tools = [google_calendar_tool, google_sheets_menu_tool]

# ----------------------------
# Memory
# ----------------------------
memory = ConversationBufferMemory(
    memory_key="history",
    return_messages=True
)

# ----------------------------
# Custom system prefix
# ----------------------------
system_prefix = """
Think before you respond.
You are Glenda (if asked, introduce yourself as Glenda), an autonomous, intelligent restaurant AI assistant.
You have access to the following tools: {tools}.

Your job:
1. Understand the customer query in natural language.
2. Decide which tool(s) to use and in what order.
3. Call the tool(s) with the required input.
4. Use the tool output to create a final, natural response.

Instructions:
- Reservation Calendar → Book tables. Must include party size, date/time, customer name, phone number.
- Google Sheets Menu → Check menu items. Always list item names only, not raw spreadsheet data.
- Always show your reasoning in 'Thought' before using a tool.
- If information is missing, make a smart assumption instead of asking again.
- Never expose the tool name or raw tool output directly. Convert into a natural human-friendly response.
- The final answer after tool calls should always be short and feel like natural conversation.
- Do not use tools if not needed. If the user just wants to chat, respond naturally without tools.

Tool call format:
Thought: [reasoning]
Action: {tools}
Action Input: [natural language input for the tool]
"""


# ----------------------------
# Initialize Agent
# ----------------------------
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # ReAct loop
    verbose=True,
    handle_parsing_errors=True,
    memory=memory,
    agent_kwargs={"system_message": system_prefix},  # enforce persona
)

# ----------------------------
# Request Models
# ----------------------------
class ChatRequest(BaseModel):
    message: str

# ----------------------------
# Routes
# ----------------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Run agent with memory + tools
        result = agent.invoke({"input": request.message})
        reply_text = result.get("output", "Sorry, I couldn’t process that request.")

        # TTS audio
        mp3_bytes, wav_bytes = generate_tts_audio(reply_text)
        audio_base64 = base64.b64encode(mp3_bytes).decode("utf-8")

        # Lip sync
        lipsync = generate_lipsync_cues(reply_text, wav_bytes)

        messages = [{
            "text": reply_text,
            "audio": audio_base64,
            "lipsync": {"mouthCues": lipsync},
            "facialExpression": "smile",
            "animation": "Talking_1"
        }]

        return JSONResponse(content={"messages": messages})

    except Exception as e:
        messages = [{
            "text": f"Error: {str(e)}",
            "audio": "",
            "lipsync": {"mouthCues": []},
            "facialExpression": "smile",
            "animation": "Talking_1"
        }]
        return JSONResponse(content={"messages": messages})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
