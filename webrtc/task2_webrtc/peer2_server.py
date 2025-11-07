from aiohttp import web
import asyncio


async def index(request):
    return web.FileResponse("peer2.html")


app = web.Application()
app.router.add_get("/", index)
web.run_app(app, port=8001)
