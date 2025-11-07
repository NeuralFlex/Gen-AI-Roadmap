import json
from aiohttp import web, WSMsgType

rooms = {}


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    room = request.query.get("room", "room1")
    if room not in rooms:
        rooms[room] = []
    rooms[room].append(ws)
    print(f"✅ Peer joined {room} (count={len(rooms[room])})")

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            data = json.loads(msg.data)
            for peer in rooms[room]:
                if peer != ws:
                    await peer.send_json(data)

    rooms[room].remove(ws)
    print(f"❌ Peer left {room}")
    return ws


app = web.Application()
app.router.add_get("/ws", websocket_handler)

print("🌐 Signaling server running on ws://localhost:9000/ws")
web.run_app(app, host="0.0.0.0", port=9000)
