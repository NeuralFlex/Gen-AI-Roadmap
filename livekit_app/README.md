
# MeetLite (Web Version)

A lightweight web-based video meeting application powered by **LiveKit**.
It allows users to **create and join video meetings** using a **passcode system**, dynamically generates meeting rooms, manages participant identities, and provides a clean, Google Meet-like interface for audio/video conferencing.

---

## 📘 Table of Contents

1. [Core Components](#core-components)
2. [Installation](#installation)
   2.1 [Prerequisites](#prerequisites)
   2.2 [Environment Configuration](#environment-configuration)
   2.3 [Setup Steps](#setup-steps)
3. [Running the Application](#running-the-application)
   3.1 [Start the Node.js Backend](#start-the-nodejs-backend)
   3.2 [Start the React Frontend](#start-the-react-frontend)
   3.3 [Workflow Summary](#workflow-summary)

---

## 1. Core Components

### 1.1 Meeting Room Management

* Backend generates **unique rooms** with **random passcodes**.
* Passcodes are shared with participants to join the meeting.
* Ensures only users with the correct passcode can join a given meeting.

### 1.2 Participant Identity

* Prompts users for their **name** upon creating or joining a meeting.
* Names are passed to LiveKit so each participant is correctly identified in the session.

### 1.3 LiveKit Video & Audio

* Uses **LiveKitServer SDK** to generate access tokens for room entry.
* Frontend uses **LiveKit React Components** to render audio/video streams in a conference layout.

### 1.4 Frontend (React)

* **HomePage**: Landing page where users can create or join a meeting.
* **MeetingPage**: Video conferencing page that displays all participants and handles audio/video streams.
* Styled with custom CSS for a clean, user-friendly interface.

### 1.5 Backend (Node.js + Express)

* Provides **REST endpoints**:

  * `/create-room`: Generates a new meeting with passcode.
  * `/join-room`: Verifies passcode and returns room info.
  * `/token`: Generates LiveKit access token for participants.
* Stores passcode → room mappings in memory (or database if extended).

---

## 2. Installation

### 2.1 Prerequisites

* Node.js 18+
* npm
* React 18+ (via create-react-app)
* LiveKit Cloud account and API credentials

### 2.2 Environment Configuration

* Create a `.env` file in the **backend folder**:

```env
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
PORT=3001
```

* Backend will use these to generate room tokens.

### 2.3 Setup Steps

```bash
# Navigate to backend
cd livekit_app/server
npm install

# Navigate to frontend
cd ../client
npm install
```

---

## 3. Running the Application

### 3.1 Start the Node.js Backend

```bash
cd livekit_app/server
node index.js
```

* Backend listens for room creation, join requests, and token generation.
* Default port: `3001`.

### 3.2 Start the React Frontend

```bash
cd livekit_app/client
npm start
```

* Opens the frontend at `http://localhost:3000` (or another port if in use).
* HomePage prompts users to **create a meeting** or **enter a passcode** to join.

---

### 3.3 Workflow Summary

1. **User creates a meeting**:

   * Enters their name → backend generates room + passcode → frontend displays passcode.
2. **User joins a meeting**:

   * Enters passcode → backend verifies it → frontend navigates to MeetingPage with token.
3. **LiveKit token** is generated per participant for secure room access.
4. **Video/Audio streams** are rendered in the browser using LiveKit React components.

✅ With this setup, you have a fully functional, web-based video meeting app with **dynamic room creation, passcode-based joining, and real-time audio/video conferencing** using LiveKit.
