from datetime import datetime
import json
import os
import re

from django.http import JsonResponse
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import (
    api_view, action, authentication_classes, permission_classes
)

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token


from . import models
from . import serializers

from openai import OpenAI

from .permissions import SoloLecturaOAdministrador



class FavoritosViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            return models.Favoritos.objects.filter(usuario=self.request.user)
        except models.Favoritos.DoesNotExist:
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
            favoritos, created = models.Favoritos.objects.get_or_create(usuario=request.user)
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
            favoritos = models.Favoritos.objects.get(usuario=request.user)
            if producto_id in favoritos.idsProductos:
                favoritos.idsProductos.remove(producto_id)
                favoritos.save()
                return Response({'favoritos': favoritos.idsProductos}, status=200)
            else:
                return Response({'error': 'Producto no encontrado en favoritos'}, status=400)
        except models.Favoritos.DoesNotExist:
            return Response({'error': 'Favoritos no encontrados para este usuario'}, status=400)

# Usuario
class UsuarioViewset(viewsets.ModelViewSet):
    queryset = models.Usuario.objects.all()
    serializer_class = serializers.UsuarioSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Se requieren email y contraseña'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Email o contraseña incorrectos'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({'error': 'Email o contraseña incorrectos'}, status=status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username
        })

@api_view(['POST'])
def realizar_pedido(request):
    if request.method == 'POST':
        serializer = serializers.PedidoSerializer(data=request.data)
        
        if serializer.is_valid():
            pedido = serializer.save()
            #serializer.save(usuario=request.user)  # asignar usuario autenticado
            return Response({'message': 'Pedido realizado con éxito', 'pedido_id': pedido.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Departamento, provincias y distritos
class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = models.Departamento.objects.all()
    serializer_class = serializers.DepartamentoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]


class ProvinciaViewSet(viewsets.ModelViewSet):
    queryset = models.Provincia.objects.all()
    serializer_class = serializers.ProvinciaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]


class DistritoViewSet(viewsets.ModelViewSet):
    queryset = models.Distrito.objects.all()
    serializer_class = serializers.DistritoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]


class EtiquetaViewSet(viewsets.ModelViewSet):
    queryset = models.Etiqueta.objects.all()
    serializer_class = serializers.EtiquetaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]


class GrupoCategoriaViewSet(viewsets.ModelViewSet):
    queryset = models.GrupoCategoria.objects.all()
    serializer_class = serializers.GrupoCategoriaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = models.Categoria.objects.all()
    serializer_class = serializers.CategoriaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]



class SubCategoriaViewSet(viewsets.ModelViewSet):
    queryset = models.SubCategoria.objects.all()
    serializer_class = serializers.SubCategoriaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = models.Producto.objects.all()
    serializer_class = serializers.ProductoSerializer
    #Filtro de nombre
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = models.Cliente.objects.all()  # necesario para el router
    serializer_class = serializers.ClienteSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return models.Cliente.objects.all()
        return models.Cliente.objects.filter(usuario=user)

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def registrarUsuario(request):
    serializer = serializers.UsuarioSerializer(data=request.data)
    
    if serializer.is_valid():
        usuario = serializer.save()
        token = Token.objects.create(user=usuario)
        return Response({
            'token': token.key,
            'usuario': {
                'user_id': usuario.id,
                'username': usuario.username,
                'email': usuario.email
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Promocion
class PromocionViewSet(viewsets.ModelViewSet):
    queryset = models.Promocion.objects.all()
    serializer_class = serializers.PromocionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]

    # Obtener todas las promociones
    def get_queryset(self):
        return models.Promocion.objects.all()

    # Acción personalizada para obtener las promociones vigentes
    @action(detail=False, methods=['get'], url_path='vigentes')
    def promociones_vigentes(self, request):
        """ Endpoint para obtener solo las promociones activas """
        promociones_activas = models.Promocion.objects.filter(fechaInicio__lte=timezone.now(), fechaFin__gte=timezone.now())
        serializer = self.get_serializer(promociones_activas, many=True)
        return Response(serializer.data)
    
# Pedido
class PedidoCreateView(APIView):
    def post(self, request, *args, **kwargs):
        pedido_data = request.data.get("pedido")
        voucher = request.FILES.get("voucher")

        if pedido_data:
            import json
            pedido_data = json.loads(pedido_data)

        serializer = serializers.PedidoSerializer(data=pedido_data)
        if serializer.is_valid():
            pedido = serializer.save()
            if voucher:
                pedido.voucher = voucher
                pedido.save()
            return Response(serializers.PedidoSerializer(pedido).data, status=201)
        return Response(serializer.errors, status=400)
    
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = models.Pedido.objects.all()
    serializer_class = serializers.PedidoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        user = self.request.user
        # Si es superusuario, ve todos los pedidos
        if user.is_superuser or user.is_staff:
            return models.Pedido.objects.all()
        # Si es usuario común, filtra por su cliente
        return models.Pedido.objects.filter(cliente__usuario=user)

    def create(self, request, *args, **kwargs):
        """
        Soporta:
        - JSON puro (application/json): body = {cliente, detalle_envio, detalle_pago, detalle_pedido, total, ...}
        - multipart/form-data: fields:
            - pedido: string JSON con la estructura anterior
            - voucher: archivo opcional
        """
        if 'pedido' in request.data:
            # Caso multipart con JSON + file
            try:
                payload = json.loads(request.data['pedido'])
            except json.JSONDecodeError:
                return Response({'detail': 'pedido inválido (JSON mal formado).'}, status=status.HTTP_400_BAD_REQUEST)

            # Si vino voucher, incrustarlo en detalle_pago
            voucher_file = request.FILES.get('voucher')
            if voucher_file:
                if 'detalle_pago' not in payload or payload['detalle_pago'] is None:
                    payload['detalle_pago'] = {}
                payload['detalle_pago']['voucher'] = voucher_file

            serializer = self.get_serializer(data=payload)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # Caso JSON puro
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()

class PruebaView(viewsets.ModelViewSet):
    queryset = models.Prueba.objects.all()
    serializer_class = serializers.PruebaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [SoloLecturaOAdministrador]

    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        serializer.save()


# OPENAI

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
        pedidos = models.Pedido.objects.filter(cliente__usuario=user)  # Obtener los pedidos del usuario

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
        productos_comprados = models.DetallePedido.objects.filter(pedido__cliente__usuario=user)  # Productos comprados

        # Construir el contexto con la información relacionada
        contexto = f"Usuario: {user.username}\n"
        contexto += "Clientes relacionados: " + ", ".join([f"{cliente.nombres} {cliente.apellidos}" for cliente in clientes]) + "\n"
        contexto += "Productos comprados: " + ", ".join([f"{producto.producto.nombre} x {producto.cantidad}" for producto in productos_comprados]) + "\n"

        # Crear el contexto con categorías, subcategorías y productos (igual que antes)
        grupos_categoria = models.GrupoCategoria.objects.all()
        categorias = models.Categoria.objects.all()
        subcategorias = models.SubCategoria.objects.all()
        productos = models.Producto.objects.all()
        etiquetas = models.Etiqueta.objects.all()

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