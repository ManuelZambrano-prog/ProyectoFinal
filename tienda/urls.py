from django.urls import path
from . import views

app_name = "tienda"

urlpatterns = [
    path("", views.home, name ="home"), 
    path("productos/", views.lista_productos, name="lista_productos"),
    path("productos/<int:pk>/", views.detalle_producto, name="detalle_producto"),
    path("productos/nuevo/", views.crear_producto, name="crear_producto"),
    path("productos/<int:pk>/editar/", views.editar_producto, name="editar_producto"),
    path("productos/<int:pk>/eliminar/", views.eliminar_producto, name="eliminar_producto"),
   
    path("pedidos/", views.lista_pedidos, name="lista_pedidos"),
    path("pedidos/nuevo-items", views.crear_pedido_items, name="crear_pedido_items"),
    path("pedidos/<int:pk>/eliminar/", views.eliminar_pedido, name="eliminar_pedido"),
    path("pedidos/<int:pk>/editar-items", views.editar_pedido_items, name="editar_pedido_items"),
    
    
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("clientes/nuevo/", views.crear_cliente, name="crear_cliente"),
    path("clientes/<int:pk>/editar/", views.editar_cliente, name="editar_cliente"),
    path("clientes/<int:pk>/eliminar/", views.eliminar_cliente, name="eliminar_cliente"),
    path("pedidos/<int:pk>/", views.detalle_pedido, name="detalle_pedido"),
    path("clientes/<int:pk>/", views.detalle_cliente, name="detalle_cliente"),

    path("buscar/", views.buscar_view, name="buscar"),
]


