
import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { AccessToken } from "livekit-server-sdk";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const { LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL } = process.env;
const rooms = new Map();

// API routes
app.post("/create-room", (req, res) => {
  const room = `room-${Date.now()}`;
  const passcode = Math.floor(100000 + Math.random() * 900000).toString();
  rooms.set(passcode, room);
  res.json({ room, passcode });
});

app.post("/join-room", (req, res) => {
  const { passcode } = req.body;
  if (!passcode) return res.status(400).json({ error: "Passcode required" });
  const room = rooms.get(passcode);
  if (!room) return res.status(404).json({ error: "Invalid passcode" });
  res.json({ room });
});

app.post("/token", async (req, res) => {
  const { room, identity } = req.body;
  if (!room || !identity) return res.status(400).json({ error: "room & identity required" });

  try {
    const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
      identity,
      name: identity,
      ttl: "2h",
    });
    at.addGrant({ roomJoin: true, room });
    const token = await at.toJwt();
    res.json({ token, url: LIVEKIT_URL, room });
  } catch (err) {
    console.error("Token generation error:", err);
    res.status(500).json({ error: "Token generation failed" });
  }
});

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const clientBuildPath = path.join(__dirname, "../client/build");

app.use(express.static(clientBuildPath));

// app.get("*", (req, res) => {
//   res.sendFile(path.join(clientBuildPath, "index.html"));
// });


const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`✅ Server running on port ${PORT}`));
