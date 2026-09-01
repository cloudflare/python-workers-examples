import os

from django_cf import DjangoCFDurableObject
from workers import DurableObject, WorkerEntrypoint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "markdown_project.settings")
from markdown_project.wsgi import application


class KnowledgeBase(DjangoCFDurableObject, DurableObject):
    def __init__(self, ctx, env):
        super().__init__(ctx, env)
        self.ctx.storage.sql.exec(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                slug VARCHAR(100) NOT NULL UNIQUE,
                body TEXT NOT NULL,
                image VARCHAR(100) NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        self.ctx.storage.sql.exec(
            "CREATE INDEX IF NOT EXISTS articles_created_at_idx ON articles (created_at DESC)"
        )

    def get_app(self):
        return application


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        id = self.env.DO_STORAGE.idFromName("knowledge-base")
        stub = self.env.DO_STORAGE.get(id)
        return await stub.fetch(request)
