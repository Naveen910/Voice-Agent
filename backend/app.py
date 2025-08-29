from fastapi import FastAPI
from asr import router as asr_router
from tts import router as tts_router
from llm import router as llm_router

app = FastAPI(title="AI Voice Agent")

# Register endpoints
app.include_router(asr_router)
app.include_router(tts_router)
app.include_router(llm_router)

@app.get("/")
def root():
    return {"message": "AI Voice Agent Backend Running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
