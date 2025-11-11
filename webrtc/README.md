```markdown
# WebRTC Tasks — Local Audio/Video Streaming

This folder contains two WebRTC tasks demonstrating **real-time audio and video streaming** between browser tabs and/or a Python server.  
**Note:** This setup is intended for local use only and is **not designed for production environments**.

---

## Task 1 — Browser ↔ Local Python Server

**Description:**  
Sets up a WebRTC connection between a browser and a local Python server. The browser captures webcam and microphone streams and sends them to the Python server. Useful for understanding how WebRTC integrates with a Python backend.

**Files:**
```

task1_webrtc/
├── client.html    # Browser client that captures and displays media
└── server.py      # Local Python server serving the client and handling streams

````

**Mechanism:**  
- Browser captures media using `getUserMedia()`.
- The Python server handles signaling and optionally relays streams.
- Manual or simple automatic offer/answer exchange establishes the connection.

**How to Run (Local Only):**
```bash
cd task1_webrtc
python3 server.py
````

* Open `client.html` in a browser to connect and stream media.

---

## Task 2 — Browser Peer-to-Peer via Signaling Server

**Description:**
Enables two browser peers, each running on separate local servers, to connect and exchange audio/video streams automatically through a Python signaling server.

**Files:**

```
task2_webrtc/
├── peer1.html            # Peer 1 client page
├── peer1_server.py       # HTTP server for Peer 1
├── peer2.html            # Peer 2 client page
├── peer2_server.py       # HTTP server for Peer 2
└── signaling_server.py   # WebSocket server for handling signaling
```

**Mechanism:**

* Each peer runs on its own local server.
* The signaling server exchanges SDP offers, answers, and ICE candidates via WebSockets.
* Once connected, peers automatically share audio and video streams.

**How to Run (Local Only):**

```bash
cd task2_webrtc
python3 signaling_server.py
python3 peer1_server.py
python3 peer2_server.py
```

* Open browser tabs for Peer 1 and Peer 2 to connect via the signaling server.

---

**Disclaimer:**
This project is intended for **local testing and learning purposes only**. It is not secure or optimized for deployment in production or over the internet.

