
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission

# Departamentos, Provincias y Distritos
class Departamento(models.Model):
    nombreDepartamento = models.CharField(max_length=100)

    def __str__(self):
        return self.nombreDepartamento

class Provincia(models.Model):
    nombreProvincia = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, related_name='provincias', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombreProvincia} ({self.departamento.nombreDepartamento})"

class Distrito(models.Model):
    nombreDistrito = models.CharField(max_length=100)
    provincia = models.ForeignKey(Provincia, related_name='distritos', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombreDistrito} ({self.provincia.nombreProvincia})"

#CATEGORIAPRODUCTO
class Etiqueta(models.Model):
    # "orgánico", "nuevo", "oferta", etc.
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

# === GRUPO ===
class GrupoCategoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre
    
# === CATEGORÍA PADRE (como Provincia) ===
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    grupo = models.ForeignKey(GrupoCategoria, related_name='categorias', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.grupo.nombre})"
    
# === SUBCATEGORÍA (como Distrito) ===
class SubCategoria(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, related_name='subcategorias', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"

class Producto(models.Model):
    id_prod = models.AutoField(primary_key=True)
    imagen = models.ImageField(upload_to='productos/')
    nombre = models.CharField(max_length=100)
    presentacion = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)
    subcategoria = models.ForeignKey(SubCategoria, related_name='productos', on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

#USUARIO
class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Correo es obligatorio')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)
#USUARIOABSTRACT
class Usuario(AbstractUser):
    objects = UsuarioManager()

    def __str__(self):
        return self.username

#CLIENTE
class Cliente(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='clientes', on_delete=models.CASCADE)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    dni = models.CharField(max_length=20)
    gmail = models.EmailField()
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} (Usuario: {self.usuario.username})"

#PEDIDO
import random
import string

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('listo', 'Listo'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, related_name='pedidos', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    idPedido = models.CharField(max_length=10, unique=True, blank=True, null=True)

    def __str__(self):
        return f"Pedido #{self.idPedido} de {self.cliente} - {self.get_estado_display()}"

    def generar_id_unico(self):
        """Genera un idPedido único compuesto por un prefijo y sufijo aleatorio"""
        while True:
            # Generar prefijo (3 letras aleatorias)
            prefijo = ''.join(random.choices(string.ascii_uppercase, k=3))
            # Generar sufijo (3 dígitos aleatorios)
            sufijo = ''.join(random.choices(string.digits, k=3))
            # Crear el idPedido (ejemplo: "ABC123")
            id_pedido = f"{prefijo}{sufijo}"
            
            # Verificar si ya existe un pedido con el mismo idPedido
            if not Pedido.objects.filter(idPedido=id_pedido).exists():
                return id_pedido

    def save(self, *args, **kwargs):
        if not self.idPedido:
            # Generar un idPedido único
            self.idPedido = self.generar_id_unico()
        super(Pedido, self).save(*args, **kwargs)

#DETALLEPEDIDO (productos + cantidad)
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='detalle_pedido', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # Para registrar precio al momento de compra

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


#ENVIO
class DetalleEnvio(models.Model):
    pedido = models.OneToOneField(Pedido, related_name='detalle_envio', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20)  # "entregaDomicilio" o "recojoTienda"

    # Datos comunes
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)
    distrito = models.ForeignKey(Distrito, on_delete=models.PROTECT)
    referencia = models.CharField(max_length=255, blank=True, null=True)

    # Solo para entrega a domicilio
    direccion = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    # Solo para recojo en tienda
    fecha = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Envio de {self.pedido} tipo {self.tipo}"


#PAGO
class DetallePago(models.Model):
    pedido = models.OneToOneField(Pedido, related_name='detalle_pago', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20) 
    card_number = models.CharField(max_length=16, blank=True, null=True)
    expiry_m = models.CharField(max_length=2, blank=True, null=True)
    expiry_a = models.CharField(max_length=2, blank=True, null=True)
    cvv = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        return f"Pago de {self.pedido}"

#FAVORITOS
class Favoritos(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='favoritos', on_delete=models.CASCADE)
    idsProductos = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"Favoritos de {self.usuario}"

