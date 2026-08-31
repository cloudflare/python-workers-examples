from django.http import HttpResponse


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = (
            "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
        )
        response["Access-Control-Allow-Headers"] = "*"
        response["Access-Control-Expose-Headers"] = "*"
        return response
