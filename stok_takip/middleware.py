from django.shortcuts import redirect

class AdminStaticFixMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/") and (
            request.path.endswith(".css")
            or request.path.endswith(".js")
            or request.path.endswith(".png")
            or request.path.endswith(".svg")
            or request.path.endswith(".ico")
        ):
            print("🛠️ AdminStaticFixMiddleware triggered for", request.path)
            return redirect("/static" + request.path)
        return self.get_response(request)
    
    
    