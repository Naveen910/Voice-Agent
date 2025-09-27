from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain.agents import initialize_agent, AgentType, Tool, ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from tools.google_calendar import google_calendar_tool
from tools.google_sheets import google_sheets_menu_tool
from speech import generate_tts_audio, generate_lipsync_cues
from langchain_google_genai import ChatGoogleGenerativeAI
import base64
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Initialize Gemini LLM
# -----------------------
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # make sure to set this
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7, google_api_key="AIzaSyBgTqN1AiBhiJZHT0CvV1jx-c099r3fMLs")

# -----------------------
# Tools for Glenda
# -----------------------
tools = [
    google_calendar_tool,
    google_sheets_menu_tool,
]

tool_names = ", ".join([t.name for t in tools])

# -----------------------
# Agent Prompt
# -----------------------
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

# -----------------------
# Memory
# -----------------------
memory = ConversationBufferMemory(memory_key="history", return_messages=True)

# -----------------------
# Initialize Agent
# -----------------------
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"prompt": prompt},
    handle_parsing_errors=True,
    memory=memory
)

# -----------------------
# Request Model
# -----------------------
class ChatRequest(BaseModel):
    message: str

# -----------------------
# Chat Endpoint
# -----------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 1️⃣ Agent reasoning + tool execution
        result = agent.invoke({"input": request.message})
        reply_text = result.get("output", "Sorry, I couldn’t process that request.")

        # 2️⃣ TTS audio
        mp3_bytes, wav_bytes = generate_tts_audio(reply_text)
        audio_base64 = base64.b64encode(mp3_bytes).decode("utf-8")

        # 3️⃣ Lip sync cues
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

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_api_based:app", host="127.0.0.1", port=5000, reload=True)
