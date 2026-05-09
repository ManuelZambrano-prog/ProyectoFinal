from django.db import models
from django.db.models import Sum, F 

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    fecha_regitro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.nombre} <{self.email}>"
    
class Pedido(models.Model):
    ESTADOS = [
        ("CREADO", "Creado"),
        ("PAGADO", "Pagado"),
        ("ENVIADO", "Enviado"),
        ("CERRADO", "Cerrado"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pedidos")
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=7, choices=ESTADOS ,default="CREADO")

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente.nombre} ({self.estado})"

    def total_productos(self):
        """Suma de las cantidades de todos los items del pedido"""
        resultado = self.items.aggregate(total=Sum('cantidad'))['total']
        return resultado if resultado is not None else 0

    def total_precio(self):
        """Suma del precio total (cantidad * precio_unitario) de todos los items"""
        resultado = self.items.aggregate(total=Sum(F('cantidad') * F('precio_unitario')))['total']
        return resultado if resultado is not None else 0

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="items")
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        '''
        Nos se permitirá que exitan dos filas con la misma combinación de pedido y producto, 
        es decir, un mismo producto no puede aparecer dos veces en el mismo pedido. 
        Esto garantiza la integridad de los datos y evita duplicados innecesarios 
        en la tabla PedidoItem.
        '''

        unique_together = ("pedido", "producto")
