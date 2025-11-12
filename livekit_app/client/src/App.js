// src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./screens/HomePage";
import MeetingPage from "./screens/MeetingPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/meeting/:roomId" element={<MeetingPage />} />
      </Routes>
    </Router>
  );
}

export default App;
