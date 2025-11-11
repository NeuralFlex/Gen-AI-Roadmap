import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { AccessToken } from 'livekit-server-sdk';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const { LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL } = process.env;

app.post('/token', async (req, res) => {
  const { room, identity } = req.body;
  if (!room || !identity) {
    return res.status(400).json({ error: 'room & identity required' });
  }

  const at = new AccessToken(
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    {
      identity: identity,
      name: identity,
      ttl: '2h',
    }
  );

  at.addGrant({
    roomJoin: true,
    room: room,
 
  });

  const token = await at.toJwt();
  res.json({ token, url: LIVEKIT_URL, room });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Token server listening on port ${PORT}`);
});
