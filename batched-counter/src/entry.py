from constants import REACTIONS

# Side effect: register the Durable Object class with the Workers runtime
from room import ReactionRoom  # noqa: F401
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from workers import asgi


def room_stub(request: Request):
    room = request.path_params["room"]
    rooms = request.scope["env"].REACTION_ROOMS
    return room, rooms.get(rooms.idFromName(room))


async def add_reaction(request: Request):
    room, stub = room_stub(request)
    reaction = request.path_params["reaction"]
    if reaction not in REACTIONS:
        return JSONResponse({"error": "Unknown reaction"}, status_code=400)
    return JSONResponse(await stub.add_reaction(room, reaction), status_code=202)


async def get_stats(request: Request):
    room, stub = room_stub(request)
    return JSONResponse(await stub.get_stats(room))


app = Starlette(
    routes=[
        Route(
            "/rooms/{room}/reactions/{reaction}",
            add_reaction,
            methods=["POST"],
        ),
        Route("/rooms/{room}/stats", get_stats, methods=["GET"]),
    ]
)

Default = asgi.entrypoint(app)
