import { createContext, useContext, useEffect, useState } from "react";

const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const [audioToPlay, setAudioToPlay] = useState(null);

  const chat = async (userMessage) => {
  setLoading(true);
  setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

  const data = await fetch(`${backendUrl}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userMessage }),
  });

  const resp = (await data.json()).messages;
  resp.forEach((reply) => {
    setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    // Prepare audio for playback
    if (reply.audio) setAudioToPlay(reply.audio);
  });

  setLoading(false);
};

  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        messages,   // expose all messages so UI can render chat history
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
        audioToPlay, 
        setAudioToPlay,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};
