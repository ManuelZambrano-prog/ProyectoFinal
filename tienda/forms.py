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
    origen = forms.CharField(required=True)
    destino = forms.CharField(required=True)
    tipo_carga = forms.CharField(required=True)

    class Meta:
        model = Pedido
        fields = ["cliente", "estado", "origen", "destino", "tipo_carga", "peso_kg"]
        widgets = {
            "origen": forms.TextInput(attrs={
                "placeholder": "Ciudad de origen"
            }),
            "destino": forms.TextInput(attrs={
                "placeholder": "Ciudad de destino"
            }),
            "tipo_carga": forms.TextInput(attrs={
                "placeholder": "Tipo de carga"
            }),
            "peso_kg": forms.NumberInput(attrs={
                "min": "0.01",
                "step": "0.01",
                "placeholder": "Peso en kilogramos"
            }),
        }

    def __init__(self, *args, **kwargs):
        opciones = kwargs.pop("opciones", None)
        super().__init__(*args, **kwargs)

        if opciones is not None:
            tipos = opciones.get("tipos_carga", [])
            origenes = opciones.get("origenes", [])
            destinos = opciones.get("destinos", [])

            if tipos:
                self.fields["tipo_carga"] = forms.ChoiceField(
                    choices=[("", "Selecciona el tipo de carga")] + [(item, item) for item in tipos],
                    required=True,
                )
            if origenes:
                self.fields["origen"] = forms.CharField(
                    widget=forms.TextInput(attrs={
                        "placeholder": "Ciudad de origen",
                        "list": "origenes_list"
                    }),
                    required=True,
                )
            if destinos:
                self.fields["destino"] = forms.CharField(
                    widget=forms.TextInput(attrs={
                        "placeholder": "Ciudad de destino",
                        "list": "destinos_list"
                    }),
                    required=True,
                )

    def clean_peso_kg(self):
        peso = self.cleaned_data.get("peso_kg")
        if peso is not None and peso <= 0:
            raise forms.ValidationError("El peso debe ser mayor que cero.")
        return peso


class ViajeForm(forms.Form):
    origen = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "placeholder": "Ciudad de origen"
        }),
    )
    destino = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "placeholder": "Ciudad de destino"
        }),
    )
    tipo_carga = forms.ChoiceField(choices=[], required=True)
    peso_kg = forms.DecimalField(
        min_value=0.01,
        decimal_places=2,
        max_digits=8,
        widget=forms.NumberInput(attrs={
            "placeholder": "Peso en kilogramos",
            "step": "0.01"
        }),
    )

    def __init__(self, *args, **kwargs):
        opciones = kwargs.pop("opciones", None)
        super().__init__(*args, **kwargs)
        tipos = []
        if opciones is not None:
            tipos = opciones.get("tipos_carga", [])
            origenes = opciones.get("origenes", [])
            destinos = opciones.get("destinos", [])

            self.fields["origen"] = forms.CharField(
                max_length=200,
                widget=forms.TextInput(attrs={
                    "placeholder": "Ciudad de origen",
                    "list": "origenes_list"
                }),
                required=True,
            )
            self.fields["destino"] = forms.CharField(
                max_length=200,
                widget=forms.TextInput(attrs={
                    "placeholder": "Ciudad de destino",
                    "list": "destinos_list"
                }),
                required=True,
            )

        self.fields["tipo_carga"].choices = [("", "Selecciona el tipo de carga")] + [
            (item, item) for item in tipos
        ]


class PedidoItemsForm(forms.ModelForm):
    class Meta:
        model = PedidoItem
        fields = ["producto", "cantidad", "precio_unitario"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"min": "1","step": "1"}),
            "precio_unitario": forms.NumberInput(attrs={"min": "0","step": "0.01"}),
        }

class PedidoCompraRapidaForm(forms.Form):
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), required=True)
    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), required=True)
    cantidad = forms.IntegerField(min_value=1, initial=1)
    origen = forms.CharField(required=True)
    destino = forms.CharField(required=True)
    tipo_carga = forms.CharField(required=True)
    peso_kg = forms.DecimalField(min_value=0.01, decimal_places=2, max_digits=8)

    def __init__(self, *args, **kwargs):
        opciones = kwargs.pop("opciones", None)
        productos = kwargs.pop("productos", None)
        super().__init__(*args, **kwargs)

        if productos is not None:
            self.fields["producto"].queryset = productos

        if opciones is not None:
            tipos = opciones.get("tipos_carga", [])
            if tipos:
                self.fields["tipo_carga"] = forms.ChoiceField(
                    choices=[("", "Selecciona el tipo de carga")] + [(item, item) for item in tipos],
                    required=True,
                )
            self.fields["origen"] = forms.CharField(
                widget=forms.TextInput(attrs={
                    "placeholder": "Ciudad de origen",
                    "list": "origenes_list"
                }),
                required=True,
            )
            self.fields["destino"] = forms.CharField(
                widget=forms.TextInput(attrs={
                    "placeholder": "Ciudad de destino",
                    "list": "destinos_list"
                }),
                required=True,
            )

    def clean_peso_kg(self):
        peso = self.cleaned_data.get("peso_kg")
        if peso is not None and peso <= 0:
            raise forms.ValidationError("El peso debe ser mayor que cero.")
        return peso

PedidoItemFormSet = inlineformset_factory(
    parent_model=Pedido,
    model=PedidoItem,
    form=PedidoItemsForm,
    extra=1,  #cuantas filas "vacias" mostrar por defecto 
    can_delete=True  # Permitir borrar filas existentes
    )