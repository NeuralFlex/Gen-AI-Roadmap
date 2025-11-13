import React, { useEffect, useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import { LiveKitRoom, VideoConference } from "@livekit/components-react";
import "@livekit/components-styles";
import "./MeetingPage.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:3001";

function MeetingPage() {
  const { roomId } = useParams();
  const location = useLocation();
  const userNameFromJoin = location?.state?.userName;

  const [token, setToken] = useState(null);
  const [userName, _setUserName] = useState(userNameFromJoin || `Guest-${Math.floor(Math.random() * 1000)}`);

  useEffect(() => {
    if (!roomId || !userName) return;

    setToken(null);
    fetch(`${API_URL}/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room: roomId, identity: userName }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data && data.token) setToken(data.token);
        else console.error("Unexpected token response:", data);
      })
      .catch((err) => console.error("Token fetch error:", err));
  }, [roomId, userName]);

  if (!token)
    return (
      <div className="meeting-container">
        <p className="loading-text">Loading meeting...</p>
      </div>
    );

  return (
    <div className="meeting-container">
      <header className="meeting-header">
        <h1>MeetLite</h1>
        <p>User: <b>{userName}</b></p>
      </header>

      <div className="meeting-info-bar">
        <span>Room: <b>{roomId}</b></span>
        <span>Enjoy your meeting!</span>
      </div>

      <div className="meeting-video-area">
        <LiveKitRoom
          token={token}
          serverUrl={process.env.REACT_APP_LIVEKIT_URL || "wss://my-first-room-99jwyo28.livekit.cloud"}
          connect={true}
          video={true}
          audio={true}
          data-lk-theme="default"
          className="video-room"
        >
          <VideoConference />
        </LiveKitRoom>
      </div>
    </div>
  );
}

export default MeetingPage;
