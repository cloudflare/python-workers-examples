from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint, asgi


def build_app(env):
    from mcp.server import MCPServer

    server = MCPServer("Incident server")

    @server.tool()
    async def open_incident(title: str, severity: str) -> dict:
        """Open an incident with a title and severity, then return the new incident."""
        if len(title) > 200 or len(severity) > 32:
            return {"error": "title or severity is too long"}

        row = (
            await env.DB.prepare(
                """
                INSERT INTO incidents (title, severity)
                VALUES (?, ?)
                RETURNING id, title, severity, status, created_at, updated_at
                """
            )
            .bind(title, severity)
            .first()
        )
        return {
            "id": row.id,
            "title": row.title,
            "severity": row.severity,
            "status": row.status,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    @server.tool()
    async def add_update(id: int, note: str) -> dict:
        """Add a note to an open incident identified by id and return the update."""
        if len(note) > 4000:
            return {"error": "note is too long", "id": id}

        incident = (
            await env.DB.prepare("SELECT id FROM incidents WHERE id = ?")
            .bind(id)
            .first()
        )
        if incident is None:
            return {"error": "incident not found", "id": id}

        results = await env.DB.batch(
            [
                env.DB.prepare(
                    """
                    INSERT INTO incident_updates (incident_id, note)
                    VALUES (?, ?)
                    RETURNING id, incident_id, note, created_at
                    """
                ).bind(id, note),
                env.DB.prepare(
                    "UPDATE incidents SET updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                ).bind(id),
            ]
        )
        update = results[0].results[0]
        return {
            "id": update.id,
            "incident_id": update.incident_id,
            "note": update.note,
            "created_at": update.created_at,
        }

    @server.tool()
    async def list_open_incidents() -> list[dict]:
        """List open incidents in newest-first order, including their chronological updates."""
        rows = await env.DB.prepare(
            """
                SELECT
                    i.id AS id,
                    i.title AS title,
                    i.severity AS severity,
                    i.status AS status,
                    i.created_at AS created_at,
                    i.updated_at AS updated_at,
                    u.id AS update_id,
                    u.incident_id AS update_incident_id,
                    u.note AS update_note,
                    u.created_at AS update_created_at
                FROM incidents i
                LEFT JOIN incident_updates u ON u.incident_id = i.id
                WHERE i.status = 'open'
                ORDER BY i.created_at DESC, i.id DESC, u.created_at ASC, u.id ASC
                """
        ).all()

        incidents_by_id = {}
        result = []
        for row in rows.results:
            incident = incidents_by_id.get(row.id)
            if incident is None:
                incident = {
                    "id": row.id,
                    "title": row.title,
                    "severity": row.severity,
                    "status": row.status,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "updates": [],
                }
                incidents_by_id[row.id] = incident
                result.append(incident)
            if row.update_id is not None:
                incident["updates"].append(
                    {
                        "id": row.update_id,
                        "incident_id": row.update_incident_id,
                        "note": row.update_note,
                        "created_at": row.update_created_at,
                    }
                )
        return result

    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
    )

    return app


class Default(WorkerEntrypoint):
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        self.app = build_app(env)

    async def fetch(self, request):
        path = urlparse(request.url).path
        if path == "/mcp" and request.method == "POST":
            return await asgi.fetch(self.app, request, self.env)

        return Response("Not found", status=404)
