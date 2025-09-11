import React, { useState, useRef } from "react";
import { Mic, X } from "lucide-react";
import "./App.css";

function App() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const recognitionRef = useRef(null);

  const startListening = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Your browser doesn't support Speech Recognition.");
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
        // send transcript to backend
        const res = await fetch("http://localhost:5000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: transcript }),
        });
        const data = await res.json();
        setResponse(data.reply);

        // Speak back
        const utterance = new SpeechSynthesisUtterance(data.reply);
        speechSynthesis.speak(utterance);
      }
    };

    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  return (
    <div className="app-container">
      <div className="content">
        {/* Mic Circle */}
        <div className="mic-wrapper">
          <div className={`mic-glow ${isListening ? "active" : ""}`}></div>
          <div className="mic-inner" onClick={startListening}>
            <Mic size={48} className="mic-icon" />
          </div>
        </div>

        {/* Live Transcript */}
        <p className="listening-text">
          {isListening
            ? "I'm listening..."
            : transcript || "Tap the mic and say something"}
        </p>

        {/* Agent Response */}
        {response && <p className="response-text">🤖 {response}</p>}

        {/* Buttons */}
        <div className="button-group">
          <button className="circle-button" onClick={stopListening}>
            <X size={20} />
          </button>
          <button className="circle-button" onClick={startListening}>
            <Mic size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
