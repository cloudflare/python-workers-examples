import uuid

from django.db import models


def generate_todo_id():
    return str(uuid.uuid4())


class Todo(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=generate_todo_id)
    title = models.TextField(default="")
    completed = models.BooleanField(default=False)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "todos"
