from workers import WorkerEntrypoint, Response, DurableObject
from pathlib import Path
from js import WebSocketPair
import json
from urllib.parse import urlparse
from datetime import datetime, timezone


class Chatroom(DurableObject):
    """Durable Object that manages a chatroom with WebSocket connections."""

    def __init__(self, state, env):
        super().__init__(state, env)
        self.state = state
        self.env = env
        self.message_history = []  # Limited message history
        self.max_history = 50  # Maximum number of messages to keep

    async def fetch(self, request):
        """Handle incoming requests to the Durable Object."""

        # Check if this is a WebSocket upgrade request
        upgrade_header = request.headers.get("Upgrade")
        if not upgrade_header or upgrade_header.lower() != "websocket":
            # If not a WebSocket request, return an error
            return Response("Expected WebSocket upgrade", status=400)

        # Create a WebSocket pair
        client, server = WebSocketPair.new().object_values()

        # Accept the WebSocket connection - this tells the DO to handle it
        self.state.acceptWebSocket(server)

        # Send message history to the newly connected client
        if self.message_history:
            history_msg = {"type": "history", "messages": self.message_history}
            server.send(json.dumps(history_msg))

        # Send a welcome message
        welcome_msg = {
            "type": "system",
            "text": "Connected to chatroom",
            "timestamp": self.get_timestamp(),
        }
        server.send(json.dumps(welcome_msg))

        # Return the client-side WebSocket in the response
        return Response(None, status=101, web_socket=client)

    async def webSocketMessage(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)

            # Create a message object
            msg = {
                "type": "message",
                "username": data.get("username", "Anonymous"),
                "text": data.get("text", ""),
                "timestamp": self.get_timestamp(),
            }

            # Add to history
            self.message_history.append(msg)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)

            # Broadcast to all connected clients
            self.broadcast(json.dumps(msg))
        except Exception as e:
            print(f"Error handling message: {e}")

    async def webSocketClose(self, ws, code, reason, wasClean):
        """Handle WebSocket close events."""
        ws.close(code, reason)
        active_connections = len(self.state.getWebSockets())
        print(f"Client disconnected. Active sessions: {active_connections}")

    async def webSocketError(self, ws, error):
        """Handle WebSocket error events."""
        ws.close(1011, "WebSocket error")
        print(f"WebSocket error: {error}")

    def broadcast(self, message):
        """Broadcast a message to all connected clients."""
        # Get all active WebSocket connections from the state
        websockets = self.state.getWebSockets()

        # Send to all active sessions
        for ws in websockets:
            try:
                ws.send(message)
            except Exception as e:
                print(f"Error broadcasting to session: {e}")

    def get_timestamp(self):
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()


class Default(WorkerEntrypoint):
    """Main worker entry point that routes requests to the Durable Object."""

    async def fetch(self, request):
        url = urlparse(request.url)
        pathname = url.path

        # Serve the HTML page for the root path
        if pathname == "/":
            html_file = Path(__file__).parent / "chatroom.html"
            return Response(
                html_file.read_text(), headers={"Content-Type": "text/html"}
            )

        # Handle room requests: /room/<name>
        if pathname.startswith("/room/"):
            # Extract room name from path
            room_name = pathname[6:]  # Remove "/room/" prefix
            if not room_name:
                return Response("Room name required", status=400)

            # Get the Durable Object namespace
            namespace = self.env.CHATROOM

            # Create a unique ID for this room
            room_id = namespace.idFromName(room_name)
            stub = namespace.get(room_id)

            # Forward the request to the Durable Object
            return await stub.fetch(request)

        return Response(
            "Not found. Use /room/<name> to connect to a chatroom.", status=404
        )
