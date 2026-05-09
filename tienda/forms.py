from django import forms
from django.forms import inlineformset_factory
from.models import Producto, Cliente, Pedido, PedidoItem

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "descripcion", "precio"]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "placeholder": "Nombre del Producto"
            }),
            "descripcion" : forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Descripción breve"
            }),
            "precio": forms.NumberInput(attrs={
                "step": "0.01",
                "min": "0"
            }),
        }
    
    def clean_precio(self):
        # Si el precio es negativo o cero, se lanza una excepción
        precio = self.cleaned_data.get("precio")
        if precio is not None and precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor que cero.")
        return precio
    


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "email"]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "placeholder": "Nombre del Cliente"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Correo electrónico"
            }),
        }


class PedidoSimpleForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente", "estado"]
       

class PedidoItemsForm(forms.ModelForm):
    class Meta:
        model = PedidoItem
        fields = ["producto", "cantidad", "precio_unitario"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"min": "1","step": "1"}),
            "precio_unitario": forms.NumberInput(attrs={"min": "0","step": "0.01"}),
        }

PedidoItemFormSet = inlineformset_factory(
    parent_model=Pedido,
    model=PedidoItem,
    form=PedidoItemsForm,
    extra=1,  #cuantas filas "vacias" mostrar por defecto 
    can_delete=True  # Permitir borrar filas existentes
    )