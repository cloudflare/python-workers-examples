from pyodide.ffi import create_proxy, to_js
from js import Object
from workers import WorkerEntrypoint

# The source code of the dynamically-loaded Python Worker. In a real
# application this could be loaded from KV, R2, or any other storage.
DYNAMIC_WORKER_SOURCE = """
from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response("Hello from a dynamically-loaded Python Worker!")
"""


def _worker_code():
    """Return a JS object describing the Worker to load.

    The shape matches the `WorkerCode` interface documented at
    https://developers.cloudflare.com/dynamic-workers/api-reference/
    """
    return to_js(
        {
            "compatibilityDate": "2026-04-01",
            "compatibilityFlags": ["python_workers"],
            "mainModule": "entry.py",
            "modules": {"entry.py": DYNAMIC_WORKER_SOURCE},
        },
        dict_converter=Object.fromEntries,
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # `env.LOADER` is the Worker Loader binding configured in
        # wrangler.jsonc. `get(id, callback)` returns a stub for a Worker
        # loaded from the code returned by the callback. The runtime caches
        # the loaded isolate by `id` so the callback usually runs only once.
        worker = self.env.LOADER.get(
            "hello-python-v1",
            create_proxy(_worker_code),
        )

        # Forward the incoming request to the dynamic Worker's default
        # entrypoint and return its response unchanged. We pass the
        # underlying JS Request object so the runtime sees a proper
        # `Request`, not the Python wrapper.
        entrypoint = worker.getEntrypoint()
        return await entrypoint.fetch(request._js_request)
