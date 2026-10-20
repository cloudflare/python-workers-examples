from urllib.parse import urlparse

from pyodide.ffi import to_js
from workers import DurableObject, Response, WorkerEntrypoint


class List(DurableObject):
    async def get_messages(self):
        messages = await self.ctx.storage.get("messages")
        return messages if messages else []

    async def add_message(self, message):
        messages = await self.get_messages()
        messages.append(message)
        await self.ctx.storage.put("messages", to_js(messages))
        return


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)

        # /<list_id>/<action>[/<message>]
        parts = url.path.split("/")
        list_id = parts[1]
        action = parts[2] if len(parts) > 2 else ""
        message = parts[3] if len(parts) > 3 else ""
        usage = "Go to /<list_id>/show to see messages\nGo to /<list_id>/add/<message> to add a message"
        if list_id == "" or (action == "add" and message == ""):
            return Response(usage, status=400)

        do_id = self.env.LISTS.idFromName(list_id)
        stub = self.env.LISTS.get(do_id)

        # Note: This is adding a message via GET URL path for simplicity, in a real app, use a POST
        if action == "add":
            # message = await request.text()
            await stub.add_message(message)
            return Response("Message sent")
        elif action == "show":
            messages = await stub.get_messages()
            if not messages:
                return Response("No messages")

            return Response("\n".join(messages))
        else:
            return Response("Not Found", status=404)
