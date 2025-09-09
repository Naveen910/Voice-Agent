import React from "react";
import { Mic, X } from "lucide-react";
import "./App.css"; // import the stylesheet

function App() {
  return (
    <div className="app-container">
      <div className="content">
        
        {/* Mic Circle */}
        <div className="mic-wrapper">
          <div className="mic-glow"></div>
          <div className="mic-inner">
            <Mic size={48} className="mic-icon" />
          </div>
        </div>

        {/* Text */}
        <p className="listening-text">
          I'm listening. <br /> What’s on your mind?
        </p>

        {/* Buttons */}
        <div className="button-group">
          <button className="circle-button">
            <X size={20} />
          </button>
          <button className="circle-button">
            <Mic size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
