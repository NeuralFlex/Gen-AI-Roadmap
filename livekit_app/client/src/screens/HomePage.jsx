import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HomePage.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:3001";

function HomePage() {
  const navigate = useNavigate();

  const [joining, setJoining] = useState(false);
  const [passcode, setPasscode] = useState("");
  const [createdMeeting, setCreatedMeeting] = useState(null);
  const [creatorName, setCreatorName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCreateMeeting = async () => {
    const userName = prompt("Enter your name:") || `Guest-${Math.floor(Math.random() * 1000)}`;
    if (!userName) return;

    setCreatorName(userName);
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/create-room`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity: userName }),
      });
      const data = await res.json();
      if (data.room && data.passcode) {
        setCreatedMeeting(data);
      } else {
        setError("Failed to create meeting");
      }
    } catch (err) {
      setError("Server error: " + err.message);
    }
    setLoading(false);
  };

  const handleJoinMeeting = async () => {
    if (!passcode) return setError("Please enter a passcode");

    const userName = prompt("Enter your name:") || `Guest-${Math.floor(Math.random() * 1000)}`;
    if (!userName) return;

    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/join-room`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ passcode, identity: userName }),
      });
      const data = await res.json();
      if (data.room) {
        navigate(`/meeting/${data.room}`, { state: { userName } });
      } else {
        setError("Invalid passcode");
      }
    } catch (err) {
      setError("Server error: " + err.message);
    }
    setLoading(false);
  };

  return (
    <div className="home-container">
      <h1 className="home-title">Welcome to MeetLite</h1>

      {!createdMeeting ? (
        <>
          {!joining ? (
            <div className="button-group">
              <button
                className="button create-btn"
                onClick={handleCreateMeeting}
                disabled={loading}
              >
                {loading ? "Creating..." : "Create New Meeting"}
              </button>
              <button
                className="button join-btn"
                onClick={() => setJoining(true)}
              >
                Join Existing Meeting
              </button>
            </div>
          ) : (
            <div className="join-section">
              <input
                type="text"
                placeholder="Enter passcode"
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                className="passcode-input"
              />
              <div className="button-group-vertical">
                <button
                  className="button create-btn"
                  onClick={handleJoinMeeting}
                  disabled={loading}
                >
                  {loading ? "Joining..." : "Join"}
                </button>
                <button
                  className="button join-btn"
                  onClick={() => setJoining(false)}
                >
                  Back
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="meeting-card">
          <h2>Meeting Created!</h2>
          <p><b>Room ID:</b> {createdMeeting.room}</p>
          <p><b>Passcode:</b> {createdMeeting.passcode}</p>
          <p className="share-info">
            Share this passcode with others to join.
          </p>
          <button
            className="button create-btn"
            onClick={() =>
              navigate(`/meeting/${createdMeeting.room}`, {
                state: { userName: creatorName },
              })
            }
          >
            Join Meeting Now
          </button>
        </div>
      )}

      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

export default HomePage;
