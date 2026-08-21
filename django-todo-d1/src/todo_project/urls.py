from django.urls import path
from todos.views import health_view, todo_detail_view, todo_list_view

urlpatterns = [
    path("api/health/", health_view),
    path("api/todos/", todo_list_view),
    path("api/todos/<int:todo_id>/", todo_detail_view),
]
