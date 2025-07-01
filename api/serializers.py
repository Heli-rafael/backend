from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from .models import (
    Departamento, Provincia, Distrito,
    Categoria, Producto,
    Cliente, Pedido, DetallePedido,
    DetalleEnvio, DetallePago, Etiqueta, GrupoCategoria, SubCategoria, Favoritos
)
from . import models
from rest_framework.exceptions import AuthenticationFailed


User = get_user_model()

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = '__all__'

class ProvinciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provincia
        fields = '__all__'

class DistritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distrito
        fields = '__all__'

class EtiquetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etiqueta
        fields = '__all__'

class GrupoCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoCategoria
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class SubCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoria
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        # Verificar si el usuario existe por email
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("El correo electrónico no existe.")

        # Validar la contraseña
        if not user.check_password(password):
            raise AuthenticationFailed("Contraseña incorrecta.")

        return {'user': user}

# Registro
class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_superuser = serializers.BooleanField(default=False)  # Puedes eliminarlo si no lo vas a pasar en el registro.

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_superuser']

    def validate(self, data):
        if not data.get('username'):
            raise ValidationError("El nombre de usuario es obligatorio.")
        if not data.get('email'):
            raise ValidationError("El correo electrónico es obligatorio.")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)  # Crea el usuario normal

        user.set_password(password)
        user.save()

        return user



#USUARIO
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Usuario
        fields = '__all__'

    def create(self, validated_data):
        user = models.Usuario(
            email = validated_data['email'],
            username = validated_data['username'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'precio_unitario']

class DetalleEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleEnvio
        fields = ['tipo', 'departamento', 'provincia', 'distrito', 'referencia', 'direccion', 'postal_code', 'fecha']

class DetallePagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePago
        fields = ['tipo', 'card_number', 'expiry_m', 'expiry_a', 'cvv']

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['nombres', 'apellidos', 'dni', 'gmail', 'telefono']

class FavoritosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favoritos
        fields = ['usuario', 'idsProductos']

class PedidoSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer()  # Datos completos del cliente
    detalle_envio = DetalleEnvioSerializer()
    detalle_pago = DetallePagoSerializer()
    detalle_pedido = DetallePedidoSerializer(many=True)
    usuario_id = serializers.SerializerMethodField()
    estado = serializers.CharField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    idPedido = serializers.CharField(read_only=True)

    class Meta:
        model = Pedido
        fields = ['idPedido', 'usuario_id', 'cliente', 'total', 'detalle_pedido', 'detalle_envio', 'detalle_pago', 'estado', 'fecha_creacion']
    
    def get_usuario_id(self, obj):
        # Este método extrae el ID del usuario del cliente asociado al pedido
        return obj.cliente.usuario.id if obj.cliente.usuario else None
    
    def create(self, validated_data, usuario=None):

        # Separar datos anidados
        cliente_data = validated_data.pop('cliente')
        detalle_envio_data = validated_data.pop('detalle_envio')
        detalle_pago_data = validated_data.pop('detalle_pago')
        detalle_pedido_data = validated_data.pop('detalle_pedido')

        # Obtener el usuario actual desde el contexto de la solicitud
        usuario = self.context['request'].user
        dni = cliente_data['dni']

        # Buscar cliente por usuario + dni. Si no existe, lo crea.
        cliente, creado = Cliente.objects.get_or_create(
            dni=dni,
            usuario=usuario,
            defaults=cliente_data
        )

        # Si el cliente ya existe, actualizamos sus datos con los nuevos (opcional)
        if not creado:
            for attr, value in cliente_data.items():
                setattr(cliente, attr, value)
            cliente.save()

        # Crear el pedido
        pedido = Pedido.objects.create(cliente=cliente, **validated_data)

        # Crear detalles de envío y pago
        DetalleEnvio.objects.create(pedido=pedido, **detalle_envio_data)
        DetallePago.objects.create(pedido=pedido, **detalle_pago_data)

        # Procesar detalles del pedido
        for detalle in detalle_pedido_data:
            producto = detalle['producto']
            cantidad = detalle['cantidad']

            # Validar stock
            if producto.stock < cantidad:
                raise ValidationError({'stock': f'No hay suficiente stock para el producto {producto.nombre}'})

            # Descontar stock y guardar
            producto.stock -= cantidad
            producto.save()

            # Crear detalle del pedido
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )

        return pedido

