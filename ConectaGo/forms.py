from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo',
        max_length=254,
        widget=forms.EmailInput(attrs={'autofocus': True, 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput
    )

# Formulario de registro para clientes
class ClientRegistrationForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre')
    apellido = forms.CharField(max_length=100, label='Apellido')
    ubicacion = forms.CharField(max_length=100, label='Ubicación')
    email = forms.EmailField(label='Correo')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

# Formulario de registro para profesionales
class ProfessionalRegistrationForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre')
    apellido = forms.CharField(max_length=100, label='Apellido')
    latitud = forms.FloatField(label='Latitud', required=False)
    longitud = forms.FloatField(label='Longitud', required=False)
    telefono = forms.CharField(max_length=20, label='Teléfono', required=False)
    email = forms.EmailField(label='Correo')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

# Formulario para editar perfil de administrador
class AdminProfileForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre')
    apellido = forms.CharField(max_length=100, label='Apellido')
    foto = forms.ImageField(label='Foto de Perfil', required=False)
    email = forms.EmailField(label='Correo')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña', required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña', required=False)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password or confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

# Formulario para editar perfil de cliente
class ClientProfileForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre')
    apellido = forms.CharField(max_length=100, label='Apellido')
    ubicacion = forms.CharField(max_length=100, label='Ubicación')
    foto = forms.ImageField(label='Foto de Perfil', required=False)
    email = forms.EmailField(label='Correo')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña', required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña', required=False)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password or confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

# Formulario para editar perfil de profesional
class ProfessionalProfileForm(forms.Form):
    nombre = forms.CharField(max_length=100, label='Nombre')
    apellido = forms.CharField(max_length=100, label='Apellido')
    especialidad = forms.CharField(max_length=100, label='Especialidad')
    latitud = forms.FloatField(label='Latitud', required=False)
    longitud = forms.FloatField(label='Longitud', required=False)
    telefono = forms.CharField(max_length=20, label='Teléfono', required=False)
    descripcion = forms.CharField(widget=forms.Textarea, required=False, label='Descripción')
    foto = forms.ImageField(label='Foto de Perfil', required=False)
    nombre_certificado = forms.CharField(max_length=200, label='Nombre Certificado', required=False)
    entidad_emisora = forms.CharField(max_length=200, label='Entidad Emisora', required=False)
    fecha_emision = forms.DateField(label='Fecha Emisión', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    archivo_pdf = forms.FileField(label='Archivo PDF', required=False)
    email = forms.EmailField(label='Correo')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña', required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirmar Contraseña', required=False)
    calendly_event_uri = forms.CharField(max_length=255, required=False, label='Calendly Event URI')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password or confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

# New form for reporting a review
class ReportForm(forms.Form):
    justification = forms.CharField(
        label='Justificación',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Por favor, indique la razón del reporte'}),
        max_length=1000,
        required=True
    )
