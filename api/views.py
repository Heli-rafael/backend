from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.authentication import TokenAuthentication

from . import models
from . import serializers

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import (
    Departamento, Provincia, Distrito,
    Categoria, Producto,
    Cliente, Pedido, DetallePedido, GrupoCategoria, SubCategoria, Etiqueta, Favoritos
)

from .serializers import (
    DepartamentoSerializer, ProvinciaSerializer, DistritoSerializer,
    CategoriaSerializer, ProductoSerializer,
    ClienteSerializer, PedidoSerializer, EtiquetaSerializer, 
    GrupoCategoriaSerializer, SubCategoriaSerializer, FavoritosSerializer, RegistroSerializer,
    CustomAuthTokenSerializer
)
from rest_framework import status, permissions
from rest_framework.views import APIView


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Favoritos
from django.contrib.auth import authenticate


class FavoritosViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            return Favoritos.objects.filter(usuario=self.request.user)
        except Favoritos.DoesNotExist:
            return []

    def list(self, request):
        favoritos = self.get_queryset()
        if favoritos:
            return Response({'favoritos': favoritos[0].idsProductos})
        else:
            return Response({'favoritos': []}, status=200)

    @action(detail=False, methods=['post'])
    def agregar(self, request):
        producto_id = request.data.get('productoId')

        if not producto_id:
            return Response({'error': 'El id del producto es requerido'}, status=400)

        try:
            favoritos, created = Favoritos.objects.get_or_create(usuario=request.user)
            if producto_id not in favoritos.idsProductos:
                favoritos.idsProductos.append(producto_id)
                favoritos.save()
                return Response({'favoritos': favoritos.idsProductos}, status=200)
            return Response({'favoritos': favoritos.idsProductos}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['delete'])
    def eliminar(self, request):
        producto_id = request.data.get('productoId')

        if not producto_id:
            return Response({'error': 'El id del producto es requerido'}, status=400)

        try:
            favoritos = Favoritos.objects.get(usuario=request.user)
            if producto_id in favoritos.idsProductos:
                favoritos.idsProductos.remove(producto_id)
                favoritos.save()
                return Response({'favoritos': favoritos.idsProductos}, status=200)
            else:
                return Response({'error': 'Producto no encontrado en favoritos'}, status=400)
        except Favoritos.DoesNotExist:
            return Response({'error': 'Favoritos no encontrados para este usuario'}, status=400)

# Usuario
class UsuarioViewset(viewsets.ModelViewSet):
    queryset = models.Usuario.objects.all()
    serializer_class = serializers.UsuarioSerializer

class CustomAuthToken(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomAuthTokenSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'email': user.email,
                'username': user.username
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def realizar_pedido(request):
    if request.method == 'POST':
        serializer = PedidoSerializer(data=request.data)
        
        if serializer.is_valid():
            pedido = serializer.save()
            #serializer.save(usuario=request.user)  # asignar usuario autenticado
            return Response({'message': 'Pedido realizado con éxito', 'pedido_id': pedido.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Departamento, provincias y distritos
class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [AllowAny]
    authentication_classes =[]

class ProvinciaViewSet(viewsets.ModelViewSet):
    queryset = Provincia.objects.all()
    serializer_class = ProvinciaSerializer
    permission_classes = [AllowAny]
    authentication_classes =[]

class DistritoViewSet(viewsets.ModelViewSet):
    queryset = Distrito.objects.all()
    serializer_class = DistritoSerializer
    permission_classes = [AllowAny]
    authentication_classes =[]

class EtiquetaViewSet(viewsets.ModelViewSet):
    queryset = Etiqueta.objects.all()
    serializer_class = EtiquetaSerializer
    permission_classes = [AllowAny]
    authentication_classes =[]

class GrupoCategoriaViewSet(viewsets.ModelViewSet):
    queryset = GrupoCategoria.objects.all()
    serializer_class = GrupoCategoriaSerializer
    permission_classes = [AllowAny]
    authentication_classes =[]

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]
    authentication_classes =[]


class SubCategoriaViewSet(viewsets.ModelViewSet):
    queryset = SubCategoria.objects.all()
    serializer_class = SubCategoriaSerializer
    permission_classes = [AllowAny]
    authentication_classes =[]

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    #Filtro de nombre
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']
    permission_classes = [AllowAny]
    authentication_classes =[]

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()  # necesario para el router
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        # filtrar para que solo vea los clientes del usuario autenticado
        return Cliente.objects.filter(usuario=self.request.user)


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]  # Exigir autenticación
    authentication_classes = [TokenAuthentication]  # Usar token auth

    def perform_create(self, serializer):
        # Aquí asignas el usuario autenticado al crear el pedido
        serializer.save()


class RegistroUsuarioView(APIView):
    permission_classes = [AllowAny]  # Permitir a cualquier usuario acceder

    def post(self, request, *args, **kwargs):
        serializer = RegistroSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Generar el token de autenticación para el nuevo usuario
            token = Token.objects.create(user=user)

            # Devolvemos el token y los datos del usuario (user_id y username)
            return Response({
                "message": "Usuario creado con éxito",
                "usuario": {
                    "username": user.username,
                    "email": user.email,
                    "user_id": user.id
                },
                "token": token.key  # Este es el token que se usará para las peticiones futuras
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginUsuarioView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]  # Si es necesario para la autenticación

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'detail': 'Email y contraseña son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

        # Autenticación usando email y password
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # El usuario se autentica correctamente
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_200_OK)

        return Response({'detail': 'Credenciales incorrectas.'}, status=status.HTTP_400_BAD_REQUEST)

# OPENAI
from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
import os
import re
from .models import Producto, Categoria, SubCategoria, Etiqueta, Pedido, DetallePedido, GrupoCategoria
from datetime import datetime
# API key de OpenAI
api_key = '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'
os.environ['OPENAI_API_KEY'] = api_key
cliente_openai = OpenAI()

@api_view(['POST'])
@authentication_classes([TokenAuthentication])  # Se usa para autenticar mediante token
@permission_classes([IsAuthenticated])  # Verifica que el usuario esté autenticado
def api_openai(request):
    # Obtener el token de autorización (se recibe en los encabezados)
    token = request.headers.get('Authorization')  # El token viene en los encabezados
    print(f'Token recibido: {token}')  # Imprimir el token para ver si llega correctamente

    # Obtener al usuario autenticado (esto solo sucede si el token es válido)
    user = request.user
    print(f'Usuario autenticado: {user.username}')  # Imprimir el nombre de usuario

    # Procesar la pregunta
    pregunta = request.data.get('pregunta', '').strip()

    if not pregunta:
        return JsonResponse({'error': 'La pregunta es obligatoria'}, status=400)

    try:
        # Obtener los pedidos del usuario autenticado
        pedidos = Pedido.objects.filter(cliente__usuario=user)  # Obtener los pedidos del usuario

        # Buscar si en la pregunta se menciona algún idPedido
        import re
        # Expresión regular para identificar posibles idPedidos en la pregunta
        patron = r'[A-Za-z]{3}\d{3}'
        id_pedido_encontrado = re.search(patron, pregunta)

        if id_pedido_encontrado:
            id_pedido = id_pedido_encontrado.group(0)  # Obtener el idPedido mencionado

            # Verificar si el idPedido pertenece a un pedido del usuario
            pedido = pedidos.filter(idPedido=id_pedido).first()

            if pedido:
                # Si el pedido existe, agregamos la información del pedido a la respuesta
                respuesta_pedido = f"**Detalles del Pedido : {pedido.idPedido}:**\n"
                respuesta_pedido += f"Estado: {pedido.get_estado_display()}\n"
                respuesta_pedido += f"Total: S/ {pedido.total}\n"
                respuesta_pedido += f"Fecha del Pedido: {pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M:%S')}\n"
                return JsonResponse({'respuesta': respuesta_pedido}, status=200)
            else:
                # Si el pedido no existe, indicamos que no se encontró
                return JsonResponse({'respuesta': f"El pedido **{id_pedido}** no existe o no está asociado a tu cuenta."}, status=200)

        # Si no se encuentra un idPedido en la pregunta, proceder con la lógica de contexto normal
        clientes = user.clientes.all()  # Obtener los clientes del usuario
        productos_comprados = DetallePedido.objects.filter(pedido__cliente__usuario=user)  # Productos comprados

        # Construir el contexto con la información relacionada
        contexto = f"Usuario: {user.username}\n"
        contexto += "Clientes relacionados: " + ", ".join([f"{cliente.nombres} {cliente.apellidos}" for cliente in clientes]) + "\n"
        contexto += "Productos comprados: " + ", ".join([f"{producto.producto.nombre} x {producto.cantidad}" for producto in productos_comprados]) + "\n"

        # Crear el contexto con categorías, subcategorías y productos (igual que antes)
        grupos_categoria = GrupoCategoria.objects.all()
        categorias = Categoria.objects.all()
        subcategorias = SubCategoria.objects.all()
        productos = Producto.objects.all()
        etiquetas = Etiqueta.objects.all()

        contexto += "\nContexto de Productos y Categorías:\n"
        contexto += "Grupos de Categorías: " + ", ".join([grupo.nombre for grupo in grupos_categoria]) + "\n"
        contexto += "Categorías: " + ", ".join([categoria.nombre for categoria in categorias]) + "\n"
        contexto += "Subcategorías: " + ", ".join([subcategoria.nombre for subcategoria in subcategorias]) + "\n"
        contexto += "Productos: " + ", ".join([producto.nombre for producto in productos]) + "\n"
        contexto += "Etiquetas: " + ", ".join([etiqueta.nombre for etiqueta in etiquetas]) + "\n"

        # Concatenar la pregunta del usuario con el contexto
        pregunta_con_contexto = contexto + "\nPregunta: " + pregunta

        # Llamar a la API de OpenAI con el contexto
        respuesta = cliente_openai.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': (
                        "Eres Shotmate, un asistente virtual para una tienda online especializada en la venta de productos."
                        " Tu objetivo es ayudar a los clientes con consultas relacionadas con la tienda, productos,grupo de categorias, categorías, subcategorías, etiquetas"
                        " pedidos y otros temas relacionados con compras y ventas online. "
                        " Recuerda que los cada pedido tienen idPedido,"
                        " y si el idPedido tiene no tiene relacion con el usuario indicar que ese idPedido no existe."
                        " Si se pide recomendacion, realizar recomendaciones de los productos de forma directa, como 3 o 4 productos de la tienda e indicar si quiere informacion de alguno."
                        " No debes responder preguntas que no estén relacionadas con la tienda o la compra de productos."
                        " Si una pregunta no está relacionada con estos temas, debes indicar que no es una pregunta relacionada con la tienda online."
                    )
                },
                {
                    'role': 'user',
                    'content': pregunta_con_contexto
                }
            ]
        )

        # Obtener la respuesta generada
        contenido = respuesta.choices[0].message.content
        return JsonResponse({'respuesta': contenido}, status=200)

    except Exception as e:
        print(f"Error en OpenAI: {str(e)}")
        return JsonResponse({'error': f'Error al generar la respuesta: {str(e)}'}, status=500)