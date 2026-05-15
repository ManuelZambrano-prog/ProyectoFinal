from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Sum, F, Avg
from .models import Producto, Cliente, Pedido, PedidoItem
from .forms import (
    ProductoForm,
    ClienteForm,
    PedidoSimpleForm,
    PedidoItemFormSet,
    ViajeForm,
    PedidoCompraRapidaForm,
)
from django.views.decorators.http import require_GET
from core.ia.tiempo_viaje.predictor import buscar_productos, obtener_opciones, predecir_tiempo

'''
Vista de inicio
'''

def home(request):
    opciones = obtener_opciones()
    clientes = Cliente.objects.order_by("-fecha_regitro")[:6]
    pedidos = Pedido.objects.select_related("cliente").order_by("-fecha")[:10]
    productos = Producto.objects.order_by("nombre")

    total_clientes = Cliente.objects.count()
    total_pedidos = Pedido.objects.count()
    total_productos = Producto.objects.count()
    promedio_tiempo = Pedido.objects.exclude(tiempo_estimado__isnull=True).aggregate(
        promedio=Avg('tiempo_estimado')
    )["promedio"]

    cliente_form = ClienteForm()
    pedido_compra_form = PedidoCompraRapidaForm(opciones=opciones, productos=productos)
    viaje_form = ViajeForm(opciones=opciones)
    tiempo_estimado = None
    registro_cliente_exitoso = False
    registro_pedido_exitoso = False

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "registrar_cliente":
            cliente_form = ClienteForm(request.POST)
            if cliente_form.is_valid():
                cliente_form.save()
                registro_cliente_exitoso = True
                cliente_form = ClienteForm()
                total_clientes = Cliente.objects.count()
                clientes = Cliente.objects.order_by("-fecha_regitro")[:6]
        elif action == "registrar_compra":
            pedido_compra_form = PedidoCompraRapidaForm(
                request.POST,
                opciones=opciones,
                productos=productos,
            )
            if pedido_compra_form.is_valid():
                pedido = Pedido(
                    cliente=pedido_compra_form.cleaned_data["cliente"],
                    estado="CREADO",
                    origen=pedido_compra_form.cleaned_data["origen"],
                    destino=pedido_compra_form.cleaned_data["destino"],
                    tipo_carga=pedido_compra_form.cleaned_data["tipo_carga"],
                    peso_kg=pedido_compra_form.cleaned_data["peso_kg"],
                    tiempo_estimado=predecir_tiempo({
                        "origen": pedido_compra_form.cleaned_data["origen"],
                        "destino": pedido_compra_form.cleaned_data["destino"],
                        "tipo_carga": pedido_compra_form.cleaned_data["tipo_carga"],
                        "peso_kg": float(pedido_compra_form.cleaned_data["peso_kg"]),
                    }),
                )
                pedido.save()
                producto = pedido_compra_form.cleaned_data["producto"]
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=pedido_compra_form.cleaned_data["cantidad"],
                    precio_unitario=producto.precio,
                )
                registro_pedido_exitoso = True
                pedido_compra_form = PedidoCompraRapidaForm(opciones=opciones, productos=productos)
                total_pedidos = Pedido.objects.count()
                pedidos = Pedido.objects.select_related("cliente").order_by("-fecha")[:10]
        elif action == "consultar_tiempo":
            viaje_form = ViajeForm(request.POST, opciones=opciones)
            if viaje_form.is_valid():
                tiempo_estimado = predecir_tiempo({
                    "origen": viaje_form.cleaned_data["origen"],
                    "destino": viaje_form.cleaned_data["destino"],
                    "tipo_carga": viaje_form.cleaned_data["tipo_carga"],
                    "peso_kg": float(viaje_form.cleaned_data["peso_kg"]),
                })

    return render(request, "tienda/home.html", {
        "clientes": clientes,
        "pedidos": pedidos,
        "productos": productos,
        "total_clientes": total_clientes,
        "total_pedidos": total_pedidos,
        "total_productos": total_productos,
        "promedio_tiempo": promedio_tiempo,
        "cliente_form": cliente_form,
        "pedido_compra_form": pedido_compra_form,
        "viaje_form": viaje_form,
        "tiempo_estimado": tiempo_estimado,
        "registro_cliente_exitoso": registro_cliente_exitoso,
        "registro_pedido_exitoso": registro_pedido_exitoso,
        "opciones": opciones,
    })

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
    opciones = obtener_opciones()
    pedido = Pedido()

    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST, opciones=opciones)
        formset = PedidoItemFormSet(request.POST, instance=pedido)

        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.tiempo_estimado = predecir_tiempo({
                "origen": pedido.origen,
                "destino": pedido.destino,
                "tipo_carga": pedido.tipo_carga,
                "peso_kg": float(pedido.peso_kg or 0),
            })
            pedido.save()
            formset.instance = pedido
            formset.save()
            return redirect("tienda:detalle_pedido", pk=pedido.pk)
    else:
        pedido_form = PedidoSimpleForm(opciones=opciones)
        formset = PedidoItemFormSet(instance=pedido)

    productos = Producto.objects.all()
    productos_dict = {str(p.id): float(p.precio) for p in productos}

    return render(request, "tienda/crear_pedido_items.html", {
        "pedido_form": pedido_form,
        "formset": formset,
        "productos": productos_dict,
        "opciones": opciones,
    })

'''
Editar un pedido
'''

@transaction.atomic
def editar_pedido_items(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    opciones = obtener_opciones()

    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST, instance=pedido, opciones=opciones)
        formset = PedidoItemFormSet(request.POST, instance=pedido)
        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.tiempo_estimado = predecir_tiempo({
                "origen": pedido.origen,
                "destino": pedido.destino,
                "tipo_carga": pedido.tipo_carga,
                "peso_kg": float(pedido.peso_kg or 0),
            })
            pedido.save()
            formset.save()
            return redirect("tienda:detalle_pedido", pk=pedido.pk)
    else:
        pedido_form = PedidoSimpleForm(instance=pedido, opciones=opciones)
        formset = PedidoItemFormSet(instance=pedido)

    return render(request, "tienda/editar_pedido_items.html", {
        "pedido": pedido,
        "pedido_form": pedido_form,
        "formset": formset,
        "opciones": opciones,
    })


def calcular_tiempo_viaje(request):
    opciones = obtener_opciones()
    tiempo = None

    if request.method == "POST":
        form = ViajeForm(request.POST, opciones=opciones)
        if form.is_valid():
            datos = {
                "origen": form.cleaned_data["origen"],
                "destino": form.cleaned_data["destino"],
                "tipo_carga": form.cleaned_data["tipo_carga"],
                "peso_kg": float(form.cleaned_data["peso_kg"]),
            }
            tiempo = predecir_tiempo(datos)
    else:
        form = ViajeForm(opciones=opciones)

    return render(request, "tienda/calcular_tiempo.html", {
        "form": form,
        "tiempo": tiempo,
        "opciones": opciones,
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