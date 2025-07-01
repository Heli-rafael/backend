from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path,include

router = DefaultRouter()

# Departamentos, Provincias y Distritos
router.register('departamentos',views.DepartamentoViewSet)
router.register('provincias',views.ProvinciaViewSet)
router.register('distritos',views.DistritoViewSet)

# Etiqueta
router.register('etiquetas', views.EtiquetaViewSet)

# Categoria
router.register('grupocategorias',views.GrupoCategoriaViewSet)
router.register('categorias',views.CategoriaViewSet)
router.register('subcategorias',views.SubCategoriaViewSet)

# Producto
router.register('productos',views.ProductoViewSet)

# Cliente
router.register('clientes',views.ClienteViewSet)

# Pedido
router.register('pedidos',views.PedidoViewSet)

# Favoritos
router.register('favoritos', views.FavoritosViewSet, basename='favoritos')


urlpatterns = [
    path('',include(router.urls)),
    path('token-auth/', views.CustomAuthToken.as_view(), name='token-auth'),
    path('realizar_pedido/', views.realizar_pedido, name='realizar_pedido'),
    path('api_openai/', views.api_openai, name='api_openai'),
    path('registro/', views.RegistroUsuarioView.as_view(), name='registro_usuario'),
]