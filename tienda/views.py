from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Sum, F
from .models import Producto, Cliente, Pedido
from.forms import ProductoForm, ClienteForm, PedidoSimpleForm, PedidoItemFormSet
from tienda import models
from django.views.decorators.http import require_GET
from core.ia.tiempo_viaje.predictor import buscar_productos

'''
Vista de inicio
'''

def home(request):
    return render(request, "tienda/home.html", {})

'''
para listar los productos
'''
def lista_productos(request):
    productos = Producto.objects.all().order_by("nombre")
    return render(request, "tienda/lista_productos.html", {"productos": productos})

'''
vista para mostrar el detalle de un producto
'''
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, "tienda/detalle_producto.html", {"producto": producto})


'''
vista para mostrar los pedidos
'''

'''
vista que lista los pedidos
'''

def lista_pedidos(request):
    pedidos = Pedido.objects.select_related("cliente").prefetch_related("items").order_by("-fecha")
    return render(request, "tienda/lista_pedidos.html", {"pedidos": pedidos})

'''
vista de detalle del pedidos
'''

def detalle_pedido(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("cliente").prefetch_related("items__producto"),
        pk=pk
    )
    items = pedido.items.all()
    total_unidades = sum(it.cantidad for it in items)
    total_pedido = sum(it.cantidad * it.precio_unitario for it in items)
    for it in items:
        it.line_total = it.cantidad * it.precio_unitario
    return render(request, "tienda/detalle_pedido.html", 
                  {
                      "pedido": pedido,
                      "items": items,
                      "total_unidades": total_unidades,
                      "total_pedido": total_pedido,
                })

def eliminar_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == "POST":
        pedido.delete()
        return redirect("tienda:lista_pedidos")

    return render(request, "tienda/eliminar_pedido.html", {"pedido": pedido})

'''
Crear pedido con Items
'''
@transaction.atomic
def crear_pedido_items(request):
    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST)
        if pedido_form.is_valid():
            pedido = pedido_form.save()
            formset = PedidoItemFormSet(request.POST, instance=pedido)
            if formset.is_valid():
                formset.save()
                return redirect("tienda:detalle_pedido", pk=pedido.pk)
        else:
            pedido = Pedido()
            formset = PedidoItemFormSet(request.POST, instance=pedido)
    else:
        pedido_form = PedidoSimpleForm()
        formset = PedidoItemFormSet()

    productos = Producto.objects.all()
    productos_dict = {str(p.id): float(p.precio) for p in productos}

    return render(request, "tienda/crear_pedido_items.html",{
        "pedido_form": pedido_form,
        "formset": formset,
        "productos": productos_dict
    })

'''
Editar un pedido
'''

@transaction.atomic
def editar_pedido_items(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST, instance=pedido)
        formset = PedidoItemFormSet(request.POST, instance=pedido)
        if pedido_form.is_valid() and formset.is_valid():
            pedido_form.save()
            formset.save()
            return redirect("tienda:detalle_pedido", pk=pedido.pk)
    else:
        pedido_form = PedidoSimpleForm(instance=pedido)
        formset = PedidoItemFormSet(instance=pedido)


    return render(request, "tienda/editar_pedido_items.html", {
        "pedido": pedido,
        "pedido_form": pedido_form,
        "formset": formset,
    })

'''
vista de detalle de un cliente
'''

def detalle_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    pedidos = cliente.pedidos.select_related('cliente').prefetch_related('items').order_by('-fecha')
    return render(request, "tienda/detalle_cliente.html", {"cliente": cliente, "pedidos": pedidos})

'''
vista que lista los clientes
'''

def lista_clientes(request):
    clientes = Cliente.objects.all().order_by("nombre")
    return render(request, "tienda/lista_clientes.html", {"clientes": clientes})



'''crear, eliminar y modificar clientes'''

def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("tienda:lista_clientes")

    else:
        form = ClienteForm()

    return render(request, "tienda/crear_cliente.html", {"form": form})

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect("tienda:detalle_cliente", pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)

    return render(request, "tienda/editar_cliente.html", {"form": form, "cliente": cliente})

def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        cliente.delete()
        return redirect("tienda:lista_clientes")

    return render(request, "tienda/eliminar_cliente.html", {"cliente": cliente})




def lista_pedidos(request):
    pedidos = Pedido.objects.select_related("cliente").prefetch_related("items").order_by("-fecha")
    return render(request, "tienda/lista_pedidos.html", {"pedidos":pedidos})

    
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("tienda:lista_productos")   
    else:
        form = ProductoForm()
    
    return render(request, "tienda/crear_producto.html", {"form": form})

def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        form = ProductoForm (request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect("tienda:detalle_producto", pk=producto.pk)
    else:
        form = ProductoForm(instance=producto)

    return render(request, "tienda/editar_producto.html", {"form": form, "producto": producto,})


def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        producto.delete()
        return redirect("tienda:lista_productos")

    return render(request, "tienda/eliminar_producto.html", {"producto": producto})


#Vista para buscar

@require_GET
def buscar_view(request):
    q = request.GET.get("q", "")
    resultados = buscar_productos(q, k=5) if q else []

    return render(request, "tienda/buscar.html", {
        "q": q, 
        "resultados": resultados,
        })