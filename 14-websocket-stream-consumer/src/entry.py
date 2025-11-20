from workers import WorkerEntrypoint, Response, DurableObject
from wasmsockets.client import connect as ws_connect
import json
import time
import asyncio
from urllib.parse import urlparse

class BlueskyFirehoseConsumer(DurableObject):
    """Durable Object that maintains a persistent WebSocket connection to Bluesky Jetstream."""

    def __init__(self, state, env):
        super().__init__(state, env)
        self.websocket = None
        self.connected = False
        self.last_print_time = 0  # Track last time we printed a post
        self.consumer_task = None  # Track the message consumer task

    async def fetch(self, request):
        """Handle incoming requests to the Durable Object."""
        # If we're not connected then make sure we start a connection.
        if not self.connected:
            await self._schedule_next_alarm()
            await self._connect_to_jetstream()

        url = urlparse(request.url)
        path = url.path

        if path == "/status":
            status = "connected" if self.connected else "disconnected"
            return Response(f"Firehose status: {status}")
        else:
            return Response("Available endpoints: /status")

    async def alarm(self):
        """Handle alarm events - used to ensure that the DO stays alive and connected"""
        print("Alarm triggered - making sure we are connected to jetstream...")
        if not self.connected:
            await self._connect_to_jetstream()
        else:
            print("Already connected, skipping reconnection")

        # Schedule the next alarm to keep the DO alive
        await self._schedule_next_alarm()

    async def _schedule_next_alarm(self):
        """Schedule the next alarm to run in 1 minute to keep the DO alive."""
        # Schedule alarm for 1 minute from now, overwriting any existing alarms
        next_alarm_time = int(time.time() * 1000) + 60000
        return await self.ctx.storage.setAlarm(next_alarm_time)

    async def _connect_to_jetstream(self):
        """Connect to the Bluesky Jetstream WebSocket and start consuming events."""
        # Get the last event timestamp from storage to resume from the right position
        last_timestamp = self.ctx.storage.kv.get("last_event_timestamp")

        # Jetstream endpoint - we'll filter for posts
        # Using wantedCollections parameter to only get post events
        jetstream_url = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

        # If we have a last timestamp, add it to resume from that point
        if last_timestamp:
            jetstream_url += f"&cursor={last_timestamp}"
            print(
                f"Connecting to Bluesky Jetstream at {jetstream_url} (resuming from timestamp: {last_timestamp})"
            )
        else:
            print(
                f"Connecting to Bluesky Jetstream at {jetstream_url} (starting fresh)"
            )

        try:
            # Connect using wasmsockets - provides a websockets-like interface
            self.websocket = await ws_connect(jetstream_url)
            self.connected = True

            print("Connected to Bluesky Jetstream firehose!")
            print(
                "Filtering for: app.bsky.feed.post (post events, rate limited to 1/sec)"
            )

            # Ensure alarm is set when we connect
            await self._schedule_next_alarm()

            # Start consuming messages in the background
            self.consumer_task = asyncio.create_task(self._consume_messages())

        except Exception as e:
            print(f"Failed to connect to Jetstream: {e}")
            self.connected = False
            self.ctx.abort(f"WebSocket connection failed: {e}")

    async def _consume_messages(self):
        """Consume messages from the WebSocket connection."""
        while self.connected and self.websocket:
            # Receive message from WebSocket
            try:
                message = await self.websocket.recv()

                # Parse the JSON message
                data = json.loads(message)

                # Store the timestamp for resumption on reconnect
                time_us = data.get("time_us")
                if time_us:
                    # Store the timestamp asynchronously
                    self.ctx.storage.kv.put("last_event_timestamp", time_us)

                # Jetstream sends different event types
                # We're interested in 'commit' events which contain posts
                if data.get("kind") == "commit":
                    commit = data.get("commit", {})
                    collection = commit.get("collection")

                    # Filter for post events
                    if collection == "app.bsky.feed.post":
                        # Rate limiting: only print at most 1 per second
                        current_time = time.time()
                        if current_time - self.last_print_time >= 1.0:
                            record = commit.get("record", {})
                            print("Post record", record)

                            # Update last print time
                            self.last_print_time = current_time

            except json.JSONDecodeError as e:
                print(f"Error parsing message JSON: {e}")
            except Exception as e:
                print(f"Error processing message: {e}")
                self.connected = False
                self.ctx.abort(f"WebSocket message processing failed: {e}")



class Default(WorkerEntrypoint):
    """Main worker entry point that routes requests to the Durable Object."""

    async def fetch(self, request):
        # Get the Durable Object namespace from the environment
        namespace = self.env.BLUESKY_FIREHOSE

        # Use a fixed ID so we always connect to the same Durable Object instance
        # This ensures we maintain a single persistent connection
        id = namespace.idFromName("bluesky-consumer")
        stub = namespace.get(id)

        # Forward the request to the Durable Object
        return await stub.fetch(request)
