from django.http import JsonResponse
from django.conf import settings

class APIKeyMiddleware:
    def __init__(self,get_response):
        self.get_response = get_response
        # Rutas que NO requieren API Key
        self.exclude_paths = [
            '/api/productos/',
            '/api/grupo-categorias/',
            '/api/categorias/',
            '/api/subcategorias/',

            '/api/etiquetas/',
            '/media/productos/',

            '/api/departamentos/',
            '/api/provincias/',
            '/api/distritos/',

            '/api/clientes/',
            '/api/favoritos/',
            '/api/api_openai/',
            '/api/registro/',
            '/api/pedidos/',
            '/api/promociones/',

            '/api/registro',
            '/api/pedidos',
            '/api/productos',
            '/api/categorias',
            '/media/productos'
        ]

    def __call__(self,request):
        path = request.path_info  # URL de la petición

        # Si la ruta está en la lista de exclusión, permitir sin API Key
        if any(path.startswith(p) for p in self.exclude_paths):
            return self.get_response(request)

        # Si la ruta NO está excluida, validar API Key
        api_key = request.headers.get('X-API-KEY') 

        if api_key and api_key == settings.API_KEY:
            return self.get_response(request)
        
        return JsonResponse({"error" : "API Key Invalida"},status=403)