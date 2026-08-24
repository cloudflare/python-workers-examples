import os

from django_cf import DjangoCF
from workers import WorkerEntrypoint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "todo_project.settings")


class Default(DjangoCF, WorkerEntrypoint):
    def get_app(self):
        from todo_project.wsgi import application

        return application
