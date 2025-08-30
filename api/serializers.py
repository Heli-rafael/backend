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
    precio = serializers.FloatField()
    class Meta:
        model = Producto
        fields = '__all__'

from django.utils import timezone

def ObtenerPrecio(producto):
    ahora = timezone.now()
    promocion = producto.promociones.filter(fechaInicio__lte=ahora, fechaFin__gte=ahora).first()
    
    # Validamos que el precio de la promoción sea menor que el precio original
    if promocion and 0 < promocion.precioPromocion < producto.precio:
        return promocion.precioPromocion
    return producto.precio

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

class FavoritosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favoritos
        fields = ['usuario', 'idsProductos']
class PromocionSerializer(serializers.ModelSerializer):
    precioPromocion = serializers.FloatField()
    class Meta:
        model = models.Promocion
        fields = "__all__"

# serializers.py
class DetallePedidoSerializer(serializers.ModelSerializer):
    # producto como PK (id)
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())

    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'precio_unitario']  # aceptamos el campo, pero lo recalculamos

class DetalleEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleEnvio
        fields = [
            'tipo', 'departamento', 'provincia', 'distrito', 'referencia',
            'direccion', 'postal_code', 'fecha'
        ]

class DetallePagoSerializer(serializers.ModelSerializer):
    voucher = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = DetallePago
        fields = ['tipo', 'card_number', 'expiry_m', 'expiry_a', 'cvv', 'voucher']

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['nombres', 'apellidos', 'dni', 'gmail', 'telefono']

class PedidoSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer()
    detalle_envio = DetalleEnvioSerializer()
    detalle_pago = DetallePagoSerializer()
    detalle_pedido = DetallePedidoSerializer(many=True)

    # los siguientes campos son de solo lectura
    usuario_id = serializers.SerializerMethodField(read_only=True)
    estado = serializers.CharField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    idPedido = serializers.CharField(read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'idPedido', 'usuario_id', 'cliente', 'total',
            'detalle_pedido', 'detalle_envio', 'detalle_pago',
            'estado', 'fecha_creacion'
        ]

    def get_usuario_id(self, obj):
        return obj.cliente.usuario.id if obj.cliente and obj.cliente.usuario_id else None

    def create(self, validated_data):
        # Extraer subestructuras
        cliente_data = validated_data.pop('cliente')
        detalle_envio_data = validated_data.pop('detalle_envio')
        detalle_pago_data = validated_data.pop('detalle_pago')
        detalle_pedido_data = validated_data.pop('detalle_pedido')

        # Usuario desde request
        usuario = self.context['request'].user

        # Crear/actualizar cliente por DNI + usuario
        dni = cliente_data.get('dni')
        cliente, creado = Cliente.objects.get_or_create(
            dni=dni,
            usuario=usuario,
            defaults=cliente_data
        )
        if not creado:
            for attr, value in cliente_data.items():
                setattr(cliente, attr, value)
            cliente.save()

        # Crear pedido
        pedido = Pedido.objects.create(cliente=cliente, total=validated_data.get('total', 0))

        # Envío
        DetalleEnvio.objects.create(pedido=pedido, **detalle_envio_data)

        # Pago (si trae voucher, lo guardamos)
        DetallePago.objects.create(pedido=pedido, **detalle_pago_data)

        # Detalle de productos (recalcular total con precio actual en servidor)
        total_pedido = 0
        for det in detalle_pedido_data:
            producto = det['producto']         # ya es instancia Producto por PrimaryKeyRelatedField
            cantidad = det['cantidad']

            if producto.stock < cantidad:
                raise ValidationError({'stock': f'No hay suficiente stock para el producto {producto.nombre}'})

            # actualizar stock
            producto.stock -= cantidad
            producto.save()

            # calcular precio vigente (ignorar precio_unitario enviado)
            precio_con_descuento = ObtenerPrecio(producto)

            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_con_descuento
            )

            total_pedido += precio_con_descuento * cantidad

        # actualizar total
        pedido.total = total_pedido
        pedido.save()

        return pedido



class PruebaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Prueba
        fields = "__all__"
