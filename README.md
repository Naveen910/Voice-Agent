# Voice-Agent

Architecture:

    🎤 User (voice)
      ↓ (Speech-to-Text, e.g., Whisper)

    📝 Text Query
      ↓
    🤖 LangChain Agent (LLM + Tools)
      - Google Calendar Tool
      - Gmail Tool
      - SQL/NoSQL Database Tool
      - File Search Tool
      - Custom APIs
      ↓
    📝 Text Response
      ↓ (Text-to-Speech, e.g., OpenAI TTS / ElevenLabs)

    🔊 Spoken Output

## Example Flow:

User (voice): "Schedule a meeting with Naveen tomorrow at 10 AM and send him an email confirmation."

- Whisper → converts to text.
- LangChain Agent → interprets the intent.
- Calls Google Calendar Tool to create the event.
- Calls Gmail Tool to send confirmation.
- LLM → generates a spoken confirmation: "I’ve scheduled the meeting and sent Rahul an email."
- TTS → speaks back.
