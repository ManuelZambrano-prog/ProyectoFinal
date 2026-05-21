from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Avg
from django.http import JsonResponse
from .models import Cliente, Pedido
from .forms import (
    ClienteForm,
    PedidoSimpleForm,
    ViajeForm,
)
from core.ia.tiempo_viaje.predictor import (
    obtener_opciones,
    predecir_tiempo,
    predecir_espera_carga,
    predecir_espera_descarga,
)

'''
Vista de inicio
'''

def home(request):
    opciones = obtener_opciones()
    clientes = Cliente.objects.order_by("-fecha_regitro")[:6]
    # Excluir pedidos pendientes (estado CREADO) de la lista de "Pedidos recientes"
    pedidos = Pedido.objects.select_related("cliente").exclude(estado="CREADO").order_by("-fecha")[:10]

    total_clientes = Cliente.objects.count()
    total_pedidos = Pedido.objects.count()
    promedio_tiempo = Pedido.objects.exclude(tiempo_estimado__isnull=True).aggregate(
        promedio=Avg('tiempo_estimado')
    )["promedio"]

    cliente_form = ClienteForm()
    viaje_form = ViajeForm(opciones=opciones)
    tiempo_estimado = None
    registro_cliente_exitoso = False

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
        "total_clientes": total_clientes,
        "total_pedidos": total_pedidos,
        "promedio_tiempo": promedio_tiempo,
        "cliente_form": cliente_form,
        "viaje_form": viaje_form,
        "tiempo_estimado": tiempo_estimado,
        "registro_cliente_exitoso": registro_cliente_exitoso,
        "opciones": opciones,
    })

'''
vista para mostrar los pedidos
'''

'''
vista que lista los pedidos
'''

def lista_pedidos(request):
    pedidos = Pedido.objects.select_related("cliente").order_by("-fecha")
    return render(request, "tienda/lista_pedidos.html", {"pedidos": pedidos})

'''
vista de detalle del pedidos
'''

def detalle_pedido(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("cliente"),
        pk=pk
    )
    datos = {
        "origen": pedido.origen,
        "destino": pedido.destino,
        "tipo_carga": pedido.tipo_carga,
        "peso_kg": float(pedido.peso_kg or 0),
    }
    espera_carga = predecir_espera_carga(datos)
    espera_descarga = predecir_espera_descarga(datos)

    return render(request, "tienda/detalle_pedido.html", {
        "pedido": pedido,
        "espera_carga": espera_carga,
        "espera_descarga": espera_descarga,
    })

def eliminar_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == "POST":
        pedido.delete()
        return redirect("tienda:lista_pedidos")

    return render(request, "tienda/eliminar_pedido.html", {"pedido": pedido})

'''
Crear pedido
'''
@transaction.atomic
def crear_pedido_items(request):
    opciones = obtener_opciones()
    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST, opciones=opciones)
        if pedido_form.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.tiempo_estimado = predecir_tiempo({
                "origen": pedido.origen,
                "destino": pedido.destino,
                "tipo_carga": pedido.tipo_carga,
                "peso_kg": float(pedido.peso_kg or 0),
            })
            pedido.save()
            return redirect("tienda:detalle_pedido", pk=pedido.pk)
    else:
        pedido_form = PedidoSimpleForm(opciones=opciones)

    return render(request, "tienda/crear_pedido_items.html", {
        "pedido_form": pedido_form,
        "opciones": opciones,
    })


def recomendar_carga(request):
    """Endpoint AJAX que recomienda `tipo_carga` y `vehiculo` según peso y ruta."""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    origen = request.POST.get("origen", "")
    destino = request.POST.get("destino", "")
    peso_raw = request.POST.get("peso_kg", "0")
    try:
        peso = float(peso_raw or 0)
    except Exception:
        peso = 0.0

    datos = {"origen": origen, "destino": destino, "peso_kg": peso}

    # Recomendar tipo de carga basado en dataset (si existe lógica)
    tipo_recomendado = ""
    try:
        from core.ia.tiempo_viaje.predictor import cargar_recursos, obtener_opciones
        cargar_recursos()
        opciones = obtener_opciones()
        tipos = opciones.get("tipos_carga", [])
        if tipos:
            tipo_recomendado = tipos[0]
    except Exception:
        tipo_recomendado = ""

    # Recomendar vehículo según peso y tipo
    if tipo_recomendado and "peligrosa" in tipo_recomendado.lower():
        vehiculo = "Tráiler especializado"
    else:
        if peso <= 500:
            vehiculo = "Camión liviano"
        elif peso <= 2000:
            vehiculo = "Camión mediano"
        else:
            vehiculo = "Camión pesado"

    return JsonResponse({"tipo_carga": tipo_recomendado, "vehiculo": vehiculo})

'''
Editar un pedido
'''

@transaction.atomic
def editar_pedido_items(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    opciones = obtener_opciones()

    if request.method == "POST":
        pedido_form = PedidoSimpleForm(request.POST, instance=pedido, opciones=opciones)
        if pedido_form.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.tiempo_estimado = predecir_tiempo({
                "origen": pedido.origen,
                "destino": pedido.destino,
                "tipo_carga": pedido.tipo_carga,
                "peso_kg": float(pedido.peso_kg or 0),
            })
            pedido.save()
            return redirect("tienda:detalle_pedido", pk=pedido.pk)
    else:
        pedido_form = PedidoSimpleForm(instance=pedido, opciones=opciones)

    return render(request, "tienda/editar_pedido_items.html", {
        "pedido": pedido,
        "pedido_form": pedido_form,
        "opciones": opciones,
    })


def calcular_tiempo_viaje(request):
    opciones = obtener_opciones()
    tiempo = None
    espera_carga = None
    espera_descarga = None

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
            espera_carga = predecir_espera_carga(datos)
            espera_descarga = predecir_espera_descarga(datos)
    else:
        form = ViajeForm(opciones=opciones)

    return render(request, "tienda/calcular_tiempo.html", {
        "form": form,
        "tiempo": tiempo,
        "espera_carga": espera_carga,
        "espera_descarga": espera_descarga,
        "opciones": opciones,
    })

'''
vista de detalle de un cliente
'''

def detalle_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    pedidos = cliente.pedidos.select_related('cliente').order_by('-fecha')
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




    
