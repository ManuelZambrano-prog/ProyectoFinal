from django import forms
from .models import Cliente, Pedido


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
        # Mover `tipo_carga` al final para que el peso venga antes
        fields = ["cliente", "estado", "origen", "destino", "peso_kg", "tipo_carga"]
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
    peso_kg = forms.DecimalField(
        min_value=0.01,
        decimal_places=2,
        max_digits=8,
        widget=forms.NumberInput(attrs={
            "placeholder": "Peso en kilogramos",
            "step": "0.01"
        }),
    )
    tipo_carga = forms.ChoiceField(choices=[], required=True)

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


