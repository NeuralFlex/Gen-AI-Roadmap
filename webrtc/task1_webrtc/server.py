import asyncio
import json
import cv2
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

pcs = set()


async def index(request: web.Request) -> web.Response:
    """Serve the static HTML page."""
    try:
        with open("client.html", "r") as f:
            html = f.read()
        return web.Response(content_type="text/html", text=html)
    except FileNotFoundError:
        return web.Response(text="client.html not found.", status=404)
    except Exception as e:
        return web.Response(text=f"Error loading client.html: {e}", status=500)


async def offer(request: web.Request) -> web.Response:
    """Handle offer from browser and return answer."""
    try:
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        pcs.add(pc)
        print("📡 Created peer connection")

        recorder = MediaRecorder("received.mp4")

        @pc.on("track")
        def on_track(track):
            """Handle incoming media tracks."""
            print(f"🎥 Track received: {track.kind}")
            if track.kind == "video":
                recorder.addTrack(track)

                async def show_frames():
                    try:
                        while True:
                            frame = await track.recv()
                            img = frame.to_ndarray(format="bgr24")
                            cv2.imshow("Remote Stream", img)
                            if cv2.waitKey(1) & 0xFF == ord("q"):
                                break
                    except Exception as e:
                        print(f"Error displaying frames: {e}")

                asyncio.ensure_future(show_frames())

        await recorder.start()
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        print("✅ SDP exchange completed.")
        return web.json_response(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        )

    except json.JSONDecodeError:
        return web.Response(text="Invalid JSON in offer.", status=400)
    except KeyError:
        return web.Response(text="Missing 'sdp' or 'type' in request.", status=400)
    except Exception as e:
        print(f"Error handling offer: {e}")
        return web.Response(text=f"Internal Server Error: {e}", status=500)


async def on_shutdown(app: web.Application) -> None:
    """Clean up peer connections."""
    try:
        coros = [pc.close() for pc in pcs]
        await asyncio.gather(*coros)
        cv2.destroyAllWindows()
        print("✅ Cleanup complete.")
    except Exception as e:
        print(f"Error during cleanup: {e}")


app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

print("🚀 Server running on http://localhost:8080")
web.run_app(app, port=8080)
