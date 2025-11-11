// App.jsx
import React, { useEffect, useState } from "react";
import { LiveKitRoom, VideoConference } from "@livekit/components-react";
import "@livekit/components-styles";

const userName = prompt("Enter your name:") || `Guest-${Math.floor(Math.random() * 1000)}`;
const roomName = "demo-room";

function App() {
  const [token, setToken] = useState(null);

  useEffect(() => {
    fetch("http://localhost:3001/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room: roomName, identity: userName }),
    })
      .then((res) => res.json())
      .then((data) => setToken(data.token))
      .catch((err) => console.error("Token fetch error:", err));
  }, []);

  if (!token) return <p>Loading...</p>;

  return (
    <LiveKitRoom
      token={token}
      serverUrl="wss://my-first-room-99jwyo28.livekit.cloud"
      connect={true}
      video={true}
      audio={true}
      data-lk-theme="default"
    >
      <VideoConference />
    </LiveKitRoom>
  );
}

export default App;
