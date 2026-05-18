from django.urls import path
from . import views

app_name = "tienda"

urlpatterns = [
    path("", views.home, name ="home"), 
    path("pedidos/", views.lista_pedidos, name="lista_pedidos"),
    path("pedidos/nuevo-items", views.crear_pedido_items, name="crear_pedido_items"),
    path("pedidos/recomendar_carga/", views.recomendar_carga, name="recomendar_carga"),
    path("pedidos/<int:pk>/eliminar/", views.eliminar_pedido, name="eliminar_pedido"),
    path("pedidos/<int:pk>/editar-items", views.editar_pedido_items, name="editar_pedido_items"),
    
    
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("clientes/nuevo/", views.crear_cliente, name="crear_cliente"),
    path("clientes/<int:pk>/editar/", views.editar_cliente, name="editar_cliente"),
    path("clientes/<int:pk>/eliminar/", views.eliminar_cliente, name="eliminar_cliente"),
    path("pedidos/<int:pk>/", views.detalle_pedido, name="detalle_pedido"),
    path("clientes/<int:pk>/", views.detalle_cliente, name="detalle_cliente"),
    path("viaje/consultar/", views.calcular_tiempo_viaje, name="calcular_tiempo"),
]


