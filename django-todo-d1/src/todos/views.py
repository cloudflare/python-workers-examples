import json

from django.http import HttpResponse, JsonResponse

from .models import Todo


def json_error(message, status):
    return JsonResponse({"error": message}, status=status)


def serialize_todo(todo):
    return {
        "id": todo.id,
        "title": todo.title,
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat(),
    }


def parse_json_body(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, json_error("Invalid JSON body.", status=400)

    if not isinstance(payload, dict):
        return None, json_error("JSON body must be an object.", status=400)

    return payload, None


def validate_title(value):
    if not isinstance(value, str):
        return None, "The 'title' field must be a string."

    normalized = value.strip()
    if not normalized:
        return None, "The 'title' field cannot be blank."

    if len(normalized) > 200:
        return None, "The 'title' field must be 200 characters or fewer."

    return normalized, None


def validate_todo_payload(payload, *, partial):
    allowed_fields = {"title", "completed"}
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        return None, f"Unsupported field(s): {', '.join(unknown_fields)}."

    if partial and not payload:
        return None, "Provide at least one field to update."

    cleaned = {}

    if not partial and "title" not in payload:
        return None, "The 'title' field is required."

    if "title" in payload:
        title, error = validate_title(payload["title"])
        if error:
            return None, error
        cleaned["title"] = title

    if "completed" in payload:
        if not isinstance(payload["completed"], bool):
            return None, "The 'completed' field must be a boolean."
        cleaned["completed"] = payload["completed"]

    return cleaned, None


def get_todo(todo_id):
    return Todo.objects.filter(pk=todo_id).first()


def health_view(request):
    match request.method:
        case "GET":
            return JsonResponse({"status": "ok"})

        case _:
            return json_error("Method not allowed.", status=405)


def todo_list_view(request):
    match request.method:
        case "GET":
            todos = [
                serialize_todo(todo)
                for todo in Todo.objects.order_by("-created_at", "-id")[:100]
            ]
            return JsonResponse({"todos": todos})

        case "POST":
            payload, error_response = parse_json_body(request)
            if error_response is not None:
                return error_response

            cleaned, error = validate_todo_payload(payload, partial=False)
            if error:
                return json_error(error, status=400)
            assert cleaned is not None

            todo = Todo.objects.create(
                title=cleaned["title"],
                completed=cleaned.get("completed", False),
            )
            return JsonResponse({"todo": serialize_todo(todo)}, status=201)

        case _:
            return json_error("Method not allowed.", status=405)


def todo_detail_view(request, todo_id):
    match request.method:
        case "GET":
            todo = get_todo(todo_id)
            if todo is None:
                return json_error("TODO not found.", status=404)
            return JsonResponse({"todo": serialize_todo(todo)})

        case "PATCH":
            todo = get_todo(todo_id)
            if todo is None:
                return json_error("TODO not found.", status=404)

            payload, error_response = parse_json_body(request)
            if error_response is not None:
                return error_response

            cleaned, error = validate_todo_payload(payload, partial=True)
            if error:
                return json_error(error, status=400)
            assert cleaned is not None

            update_fields = []
            for field_name, value in cleaned.items():
                setattr(todo, field_name, value)
                update_fields.append(field_name)

            todo.save(update_fields=update_fields)
            return JsonResponse({"todo": serialize_todo(todo)})

        case "DELETE":
            deleted_count, _ = Todo.objects.filter(pk=todo_id).delete()
            if deleted_count == 0:
                return json_error("TODO not found.", status=404)
            return HttpResponse(status=204)

        case _:
            return json_error("Method not allowed.", status=405)
