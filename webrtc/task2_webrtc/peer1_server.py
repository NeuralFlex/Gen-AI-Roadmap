from aiohttp import web


async def index(request):
    return web.FileResponse("peer1.html")


app = web.Application()
app.router.add_get("/", index)
web.run_app(app, port=8000)
