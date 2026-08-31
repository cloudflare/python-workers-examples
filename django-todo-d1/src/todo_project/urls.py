from django.urls import path
from todos.views import todo_detail_view, todo_list_view

urlpatterns = [
    path("todos", todo_list_view),
    path("todos/<str:todo_id>", todo_detail_view),
]
