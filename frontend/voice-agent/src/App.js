import React, { useState, useRef } from "react";
import { Mic, X } from "lucide-react";
import "./App.css";
import Avatar from "./components/Avatar";

function App() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const recognitionRef = useRef(null);
  const [audioStream, setAudioStream] = useState(null);
  const [expression, setExpression] = useState("neutral");

  const startListening = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Your browser doesn’t support Speech Recognition.");
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      let text = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        text += event.results[i][0].transcript;
      }
      setTranscript(text);
    };

    recognition.onend = async () => {
      setIsListening(false);
      if (transcript) {
        const res = await fetch("http://localhost:5000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: transcript }),
        });
        const data = await res.json();
        setResponse(data.reply);

        // Pick expression
        if (data.reply.includes("!")) setExpression("angry");
        else if (data.reply.match(/great|happy|nice/i)) setExpression("smile");
        else setExpression("neutral");

        // Generate TTS with Web Audio
        const audioCtx = new AudioContext();
        const dest = audioCtx.createMediaStreamDestination();
        setAudioStream(dest.stream);

        // Example: browser TTS routed to audio element
        const utterance = new SpeechSynthesisUtterance(data.reply);
        window.speechSynthesis.speak(utterance);

        // Note: For **real-time lip-sync**, use external TTS API streaming to AudioContext
      }
    };

    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
  };

  const stopListening = () => {
    if (recognitionRef.current) recognitionRef.current.stop();
    setIsListening(false);
  };

  return (
    <div className="app-container">
      {/* Avatar */}
      <Avatar audioStream={audioStream} expression={expression} />

      

        <p className="listening-text">
          {isListening ? "I'm listening..." : transcript || "Tap the mic and say something"}
        </p>

        {response && <p className="response-text">🤖 {response}</p>}

        <div className="button-group">
          <button className="circle-button" onClick={stopListening}>
            <X size={20} />
          </button>
          <button className="circle-button" onClick={startListening}>
            <Mic size={20} />
          </button>
        </div>
      </div>
    
  );
}

export default App;
