import json

from django.http import JsonResponse

from .models import Todo


def serialize_todo(todo, request):
    collection_url = request.build_absolute_uri("/todos").rstrip("/")
    return {
        "id": str(todo.id),
        "title": todo.title,
        "completed": todo.completed,
        "order": todo.order,
        "url": f"{collection_url}/{todo.id}",
    }


def parse_json_body(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, JsonResponse({"error": "Invalid JSON body."}, status=400)

    if not isinstance(payload, dict):
        return None, JsonResponse({"error": "JSON body must be an object."}, status=400)

    return payload, None


def get_todo(todo_id):
    return Todo.objects.filter(pk=todo_id).first()


def todo_list_view(request):
    match request.method:
        case "GET":
            todos = [serialize_todo(todo, request) for todo in Todo.objects.all()]
            return JsonResponse(todos, safe=False)

        case "POST":
            payload, error_response = parse_json_body(request)
            if error_response is not None:
                return error_response
            assert payload is not None

            todo = Todo.objects.create(
                title=payload.get("title", ""),
                completed=bool(payload.get("completed", False)),
                order=payload.get("order"),
            )
            return JsonResponse(serialize_todo(todo, request))

        case "DELETE":
            Todo.objects.all().delete()
            return JsonResponse([], safe=False)

        case _:
            return JsonResponse({"error": "Method not allowed."}, status=405)


def todo_detail_view(request, todo_id):
    match request.method:
        case "GET":
            todo = get_todo(todo_id)
            if todo is None:
                return JsonResponse({"error": "not found"})
            return JsonResponse(serialize_todo(todo, request))

        case "PATCH":
            todo = get_todo(todo_id)
            if todo is None:
                return JsonResponse({"error": "not found"})

            payload, error_response = parse_json_body(request)
            if error_response is not None:
                return error_response
            assert payload is not None

            update_fields = []
            if "title" in payload:
                todo.title = payload["title"]
                update_fields.append("title")
            if "completed" in payload:
                todo.completed = bool(payload["completed"])
                update_fields.append("completed")
            if "order" in payload:
                todo.order = payload["order"]
                update_fields.append("order")

            if update_fields:
                todo.save(update_fields=update_fields)
            return JsonResponse(serialize_todo(todo, request))

        case "DELETE":
            Todo.objects.filter(pk=todo_id).delete()
            return JsonResponse([], safe=False)

        case _:
            return JsonResponse({"error": "Method not allowed."}, status=405)
