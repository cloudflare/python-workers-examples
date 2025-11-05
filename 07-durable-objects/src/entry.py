from workers import WorkerEntrypoint, Response, DurableObject
from pyodide.ffi import to_js
from urllib.parse import urlparse


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

        list_id = url.path.split("/")[1]
        if list_id == "":
            return Response(
                "Go to /<list_id>/show to see messages\nGo to /<list_id>/add/<message> to add a message",
                status=400,
            )

        do_id = self.env.LISTS.idFromName(list_id)
        stub = self.env.LISTS.get(do_id)

        # Note: This is adding a message via GET URL path for simplicity, in a real app, use a POST
        if "/add" in url.path:
            # message = await request.text()
            message = url.path.split("/")[3]
            await stub.add_message(message)
            return Response("Message sent")
        elif "/show" in url.path:
            messages = await stub.get_messages()
            if not messages:
                return Response("No messages")

            return Response("\n".join(messages))
        else:
            return Response("Not Found", status=404)
