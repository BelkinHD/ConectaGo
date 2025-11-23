from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import (
    LoginForm,
    ClientRegistrationForm,
    ProfessionalRegistrationForm,
    AdminProfileForm,
    ClientProfileForm,
    ProfessionalProfileForm,
)
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from ConectaGo.models import ProfessionalProfile, ClientProfile, AdminProfile

def home(request):
    profesion = request.GET.get('profesion', '').strip()
    ubicacion = request.GET.get('ubicacion', '').strip()

    profesionales = ProfessionalProfile.objects.all()

    if ubicacion and ubicacion != 'Todas las ubicaciones':
        profesionales = profesionales.filter(ubicacion__icontains=ubicacion)
    if profesion and profesion != 'Todas las profesiones':
        profesionales = profesionales.filter(especialidad__icontains=profesion)

    # Fetch all distinct ubicaciones and profesiones from all professionals (not filtered)
    ubicaciones = ProfessionalProfile.objects.values_list('ubicacion', flat=True).distinct()
    profesiones = ProfessionalProfile.objects.values_list('especialidad', flat=True).distinct()

    contexto = {
        'profesionales': profesionales,
        'ubicaciones': ['Todas las ubicaciones'] + list(ubicaciones),
        'profesion': profesion,
        'ubicacion': ubicacion,
        'profesiones': ['Todas las profesiones'] + list(profesiones),
    }

    if request.user.is_authenticated:
        contexto['tipo_usuario'] = 'desconocido'
    return render(request, 'vistas/home.html', contexto)

def client_register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            ubicacion = form.cleaned_data['ubicacion']
            username = email
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El correo ya está registrado.')
            else:
                with transaction.atomic():
                    user = User.objects.create_user(username=username, email=email, password=password)
                    # Set first_name and last_name for user
                    user.first_name = nombre
                    user.last_name = apellido
                    user.save()
                    # Create ClientProfile for the new user
                    from ConectaGo.models import ClientProfile
                    ClientProfile.objects.create(user=user, nombre=nombre, apellido=apellido, ubicacion=ubicacion)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('ConectaGo:home')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ClientRegistrationForm()
    return render(request, 'vistas/client_register.html', {'form': form})

def professional_register(request):
    if request.method == 'POST':
        form = ProfessionalRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            especialidad = form.cleaned_data['especialidad']
            ubicacion = form.cleaned_data['ubicacion']
            latitud = form.cleaned_data.get('latitud')
            longitud = form.cleaned_data.get('longitud')
            telefono = form.cleaned_data.get('telefono')
            if telefono:
                telefono = telefono.strip()
                if not telefono.startswith("+56 9"):
                    telefono = "+56 9 " + telefono
            if User.objects.filter(username=email).exists():
                messages.error(request, 'El correo ya está registrado.')
            else:
                with transaction.atomic():
                    user = User.objects.create_user(username=email, email=email, password=password)
                    # Set first_name and last_name for user
                    user.first_name = nombre
                    user.last_name = apellido
                    user.save()
                    # Create ProfessionalProfile for the new user
                    from ConectaGo.models import ProfessionalProfile
                    ProfessionalProfile.objects.create(
                        user=user,
                        nombre=nombre,
                        apellido=apellido,
                        especialidad=especialidad,
                        ubicacion=ubicacion,
                        latitud=latitud,
                        longitud=longitud,
                        telefono=telefono
                    )
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('ConectaGo:home')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ProfessionalRegistrationForm()
    return render(request, 'vistas/professional_register.html', {'form': form})

@login_required
def professional_profile_edit(request):
    user = request.user
    try:
        professional_profile = user.professionalprofile
    except ProfessionalProfile.DoesNotExist:
        professional_profile = None

    if request.method == 'POST':
        form = ProfessionalProfileForm(request.POST, request.FILES)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            especialidad = form.cleaned_data['especialidad']
            ubicacion = form.cleaned_data['ubicacion']
            telefono = form.cleaned_data.get('telefono')
            if telefono and not telefono.startswith("+56 9"):
                telefono = "+56 9" + telefono
            nombre_certificado = form.cleaned_data.get('nombre_certificado')
            entidad_emisora = form.cleaned_data.get('entidad_emisora')
            fecha_emision = form.cleaned_data.get('fecha_emision')
            archivo_pdf = form.cleaned_data.get('archivo_pdf')
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            foto = form.cleaned_data.get('foto')

            import requests

            def geocode_address(address, api_key):
                import logging
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                # Append ", Chile" if not present to improve geocoding accuracy
                if "chile" not in address.lower():
                    address = f"{address}, Chile"
                params = {
                    "address": address,
                    "key": api_key,
                }
                try:
                    response = requests.get(url, params=params, timeout=5)
                    response.raise_for_status()
                    data = response.json()
                    logging.info(f"Geocoding response for address '{address}': {data}")
                    if data['status'] == 'OK' and len(data['results']) > 0:
                        location = data['results'][0]['geometry']['location']
                        return location['lat'], location['lng']
                    else:
                        logging.error(f"Geocoding failed for address '{address}': {data.get('status')}")
                except Exception as e:
                    logging.error(f"Exception during geocoding for address '{address}': {e}")
                return None, None

            # Update user fields
            user.first_name = nombre
            user.last_name = apellido
            user.email = email
            user.username = email  # Assuming username is email
            user.save()

            # Update password if provided
            if password:
                user.set_password(password)
                user.save()

            # Geocode the ubicacion to get latitud and longitud
            api_key = 'AIzaSyCo9E96ubTQ8C-4KtQ1kZUXBqkJwWH5seQ'  # Ideally, get from settings or environment
            lat, lng = geocode_address(ubicacion, api_key)
            import logging
            logging.info(f"Geocoded lat: {lat}, lng: {lng} for address: {ubicacion}")

            # Update or create professional profile
            if professional_profile:
                if foto:
                    professional_profile.foto = foto
                professional_profile.nombre = nombre
                professional_profile.apellido = apellido
                professional_profile.especialidad = especialidad
                professional_profile.ubicacion = ubicacion
                professional_profile.telefono = telefono
                professional_profile.nombre_certificado = nombre_certificado
                professional_profile.entidad_emisora = entidad_emisora
                professional_profile.fecha_emision = fecha_emision
                if archivo_pdf:
                    professional_profile.archivo_pdf = archivo_pdf
                if lat is not None and lng is not None:
                    professional_profile.latitud = lat
                    professional_profile.longitud = lng
                professional_profile.save()
            else:
                professional_profile = ProfessionalProfile.objects.create(
                    user=user,
                    nombre=nombre,
                    apellido=apellido,
                    especialidad=especialidad,
                    ubicacion=ubicacion,
                    telefono=telefono,
                    nombre_certificado=nombre_certificado,
                    entidad_emisora=entidad_emisora,
                    fecha_emision=fecha_emision,
                    archivo_pdf=archivo_pdf,
                    foto=foto,
                    latitud=lat,
                    longitud=lng,
                )

            messages.success(request, 'Datos actualizados correctamente')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        initial_data = {
            'nombre': user.first_name or '',
            'apellido': user.last_name or '',
            'especialidad': professional_profile.especialidad if professional_profile else '',
            'ubicacion': professional_profile.ubicacion if professional_profile else '',
            'telefono': professional_profile.telefono if professional_profile else '',
            'nombre_certificado': professional_profile.nombre_certificado if professional_profile else '',
            'entidad_emisora': professional_profile.entidad_emisora if professional_profile else '',
            'fecha_emision': professional_profile.fecha_emision if professional_profile else None,
            # Note: archivo_pdf is a file field, usually not pre-populated in forms
            'email': user.email or '',
        }
        form = ProfessionalProfileForm(initial=initial_data)

    specialties = ProfessionalProfile.objects.values_list('especialidad', flat=True).distinct()

    contexto = {
        'form': form,
        'professional_profile': professional_profile,
        'specialties': specialties,
    }
    return render(request, 'vistas/professional_profile_edit.html', contexto)

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import LoginForm

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import LoginForm

def login_view(request):
    test_users = {
        'cliente': {'email': 'cliente@cliente.com', 'password': 'cliente123'},
        'profesional': {'email': 'profesional@profesional.com', 'password': 'profesional123'},
        'administrador': {'email': 'admin@admin.com', 'password': '1234'},
    }

    if request.method == 'POST':
        if 'test_user' in request.POST:
            user_key = request.POST['test_user']
            if user_key in test_users:
                email = test_users[user_key]['email']
                password = test_users[user_key]['password']
                user = authenticate(request, username=email, password=password, backend='ConectaGo.backends.EmailBackend')
                if user is not None:
                    if not hasattr(user, 'backend'):
                        user.backend = 'ConectaGo.backends.EmailBackend'
                    login(request, user)
                    return redirect('ConectaGo:home')
                else:
                    messages.error(request, f'No se pudo autenticar al usuario de prueba: {user_key}')
            else:
                messages.error(request, 'Usuario de prueba no válido.')
            form = LoginForm()
        else:
            form = LoginForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                user = authenticate(request, username=email, password=password, backend='ConectaGo.backends.EmailBackend')
                if user is not None:
                    if not hasattr(user, 'backend'):
                        user.backend = 'ConectaGo.backends.EmailBackend'
                    login(request, user)
                    return redirect('ConectaGo:home')
                else:
                    messages.error(request, 'Correo o contraseña incorrectos.')
    else:
        form = LoginForm()
    from django.contrib import messages as django_messages
    return render(request, 'vistas/login.html', {'form': form, 'test_users': test_users, 'messages': django_messages.get_messages(request)})


def logout_view(request):
    logout(request)
    return redirect('ConectaGo:home')

@login_required
def profile_view(request):
    return render(request, 'vistas/profile.html')

@login_required
def admin_user_list(request):
    clientes = ClientProfile.objects.exclude(user__email__iexact='admin@admin.com')
    profesionales = ProfessionalProfile.objects.exclude(user__email__iexact='admin@admin.com')
    contexto = {
        'clientes': clientes,
        'profesionales': profesionales,
    }
    return render(request, 'vistas/admin_user_list.html', contexto)

@login_required
def admin_profile_edit(request):
    user = request.user
    try:
        admin_profile = user.adminprofile
    except Exception:
        admin_profile = None

    if request.method == 'POST':
        form = AdminProfileForm(request.POST, request.FILES)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            foto = form.cleaned_data.get('foto')

            # Update user fields
            user.first_name = nombre
            user.last_name = apellido
            user.email = email
            user.username = email  # Assuming username is email
            user.save()

            # Update password if provided
            if password:
                user.password = make_password(password)
                user.save()

            # Update photo
            if admin_profile:
                if foto:
                    admin_profile.foto = foto
                    admin_profile.save()
            else:
                # Create admin profile if not exists
                admin_profile = AdminProfile.objects.create(user=user, foto=foto)

            messages.success(request, 'Datos actualizados correctamente')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        initial_data = {
            'nombre': user.first_name,
            'apellido': user.last_name,
            'email': user.email,
        }
        form = AdminProfileForm(initial=initial_data)

    contexto = {
        'form': form,
        'admin_profile': admin_profile,
    }
    return render(request, 'vistas/admin_profile_edit.html', contexto)

@login_required
def client_profile_edit(request):
    user = request.user
    try:
        client_profile = user.clientprofile
    except ClientProfile.DoesNotExist:
        client_profile = None

    if request.method == 'POST':
        form = ClientProfileForm(request.POST, request.FILES)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            ubicacion = form.cleaned_data['ubicacion']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            foto = form.cleaned_data.get('foto')

            # Update user fields
            user.first_name = nombre
            user.last_name = apellido
            user.email = email
            user.username = email  # Assuming username is email
            user.save()

            # Update password if provided
            if password:
                user.password = make_password(password)
                user.save()

            # Update or create client profile
            if client_profile:
                if foto:
                    client_profile.foto = foto
                client_profile.nombre = nombre
                client_profile.apellido = apellido
                client_profile.ubicacion = ubicacion
                client_profile.save()
            else:
                client_profile = ClientProfile.objects.create(user=user, nombre=nombre, apellido=apellido, ubicacion=ubicacion, foto=foto)

            messages.success(request, 'Datos actualizados correctamente')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        initial_data = {
            'nombre': user.first_name or '',
            'apellido': user.last_name or '',
            'email': user.email or '',
            'ubicacion': client_profile.ubicacion if client_profile else '',
        }
        form = ClientProfileForm(initial=initial_data)

    contexto = {
        'form': form,
        'client_profile': client_profile,
    }
    return render(request, 'vistas/client_profile_edit.html', contexto)


@login_required
def mi_perfil_profesional_view(request):
    from django.http import Http404
    from ConectaGo.models import ProfessionalProfile

    user = request.user

    try:
        professional_profile = ProfessionalProfile.objects.get(user=user)
    except ProfessionalProfile.DoesNotExist:
        raise Http404("Perfil profesional no encontrado")

    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    form = None  # Initialize form variable

    if request.method == 'POST':
        # Check if this is a partial update for descripcion only
        if 'descripcion' in request.POST and len(request.POST) == 2:  # csrf token + descripcion
            descripcion = request.POST.get('descripcion', '').strip()
            professional_profile.descripcion = descripcion
            professional_profile.save()
            messages.success(request, 'Descripción actualizada correctamente')
            form = ProfessionalProfileForm(initial={
                'nombre': user.first_name or '',
                'apellido': user.last_name or '',
                'especialidad': professional_profile.especialidad if professional_profile else '',
                'ubicacion': professional_profile.ubicacion if professional_profile else '',
                'experiencia': professional_profile.experiencia if professional_profile else '',
                'descripcion': professional_profile.descripcion if professional_profile else '',
                'email': user.email or '',
            })
        # Check if this is a partial update for ubicacion only
        elif 'ubicacion' in request.POST and len(request.POST) == 2:  # csrf token + ubicacion
            ubicacion = request.POST.get('ubicacion', '').strip()
            professional_profile.ubicacion = ubicacion
            professional_profile.save()
            messages.success(request, 'Ubicación actualizada correctamente')
            form = ProfessionalProfileForm(initial={
                'nombre': user.first_name or '',
                'apellido': user.last_name or '',
                'especialidad': professional_profile.especialidad if professional_profile else '',
                'ubicacion': professional_profile.ubicacion if professional_profile else '',
                'experiencia': professional_profile.experiencia if professional_profile else '',
                'descripcion': professional_profile.descripcion if professional_profile else '',
                'email': user.email or '',
            })
        # Check if this is a partial update for schedule only
        elif any(key.endswith('_start') or key.endswith('_end') or key.endswith('_closed') for key in request.POST.keys()):
            schedule = {}
            for day in days:
                day_lower = day.lower()
                start = request.POST.get(f"{day_lower}_start")
                end = request.POST.get(f"{day_lower}_end")
                closed = request.POST.get(f"{day_lower}_closed") == 'on'
                schedule[day] = {
                    "start": start if not closed else None,
                    "end": end if not closed else None,
                    "closed": closed
                }
            professional_profile.schedule = schedule
            professional_profile.save()
            messages.success(request, 'Horarios actualizados correctamente')
            form = ProfessionalProfileForm(initial={
                'nombre': user.first_name or '',
                'apellido': user.last_name or '',
                'especialidad': professional_profile.especialidad if professional_profile else '',
                'ubicacion': professional_profile.ubicacion if professional_profile else '',
                'experiencia': professional_profile.experiencia if professional_profile else '',
                'descripcion': professional_profile.descripcion if professional_profile else '',
                'email': user.email or '',
            })
        else:
            form = ProfessionalProfileForm(request.POST, request.FILES)
            if form.is_valid():
                nombre = form.cleaned_data['nombre']
                apellido = form.cleaned_data['apellido']
                especialidad = form.cleaned_data['especialidad']
                ubicacion = form.cleaned_data['ubicacion']
                experiencia = form.cleaned_data.get('experiencia')
                descripcion = form.cleaned_data.get('descripcion')
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                foto = form.cleaned_data.get('foto')

                # Update user fields
                user.first_name = nombre
                user.last_name = apellido
                user.email = email
                user.username = email  # Assuming username is email
                user.save()

                # Update password if provided
                if password:
                    user.set_password(password)
                    user.save()

                # Update professional profile
                if foto:
                    professional_profile.foto = foto
                professional_profile.nombre = nombre
                professional_profile.apellido = apellido
                professional_profile.especialidad = especialidad
                professional_profile.ubicacion = ubicacion
                professional_profile.experiencia = experiencia
                professional_profile.descripcion = descripcion
                professional_profile.save()

                messages.success(request, 'Datos actualizados correctamente')
            else:
                messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        initial_data = {
            'nombre': user.first_name or '',
            'apellido': user.last_name or '',
            'especialidad': professional_profile.especialidad if professional_profile else '',
            'ubicacion': professional_profile.ubicacion if professional_profile else '',
            'experiencia': professional_profile.experiencia if professional_profile else '',
            'descripcion': professional_profile.descripcion if professional_profile else '',
            'email': user.email or '',
        }
        form = ProfessionalProfileForm(initial=initial_data)

    # Ensure schedule is always loaded fresh from professional_profile to show saved schedule
    schedule = professional_profile.schedule if professional_profile.schedule else {}

    contexto = {
        'form': form,
        'professional_profile': professional_profile,
        'schedule': schedule,
        'days': days,
    }
    return render(request, 'vistas/mi_perfil_profesional.html', contexto)

def public_professional_profile_view(request, username):
    from django.http import Http404
    try:
        user = User.objects.get(username=username)
        professional_profile = ProfessionalProfile.objects.get(user=user)
    except (User.DoesNotExist, ProfessionalProfile.DoesNotExist):
        raise Http404("Perfil profesional no encontrado")

    # Parse comuna and ciudad from ubicacion
    comuna = ''
    ciudad = ''
    if professional_profile.ubicacion:
        # Simple heuristic: split by commas and strip spaces
        parts = [part.strip() for part in professional_profile.ubicacion.split(',')]
        if len(parts) >= 2:
            comuna = parts[-2]
            ciudad = parts[-1]
        elif len(parts) == 1:
            comuna = parts[0]

    contexto = {
        'professional_profile': professional_profile,
        'google_maps_api_key': 'AIzaSyCo9E96ubTQ8C-4KtQ1kZUXBqkJwWH5seQ',  # Reemplaza con tu clave API real o configúrala dinámicamente
        'comuna': comuna,
        'ciudad': ciudad,
    }
    return render(request, 'vistas/public_professional_profile.html', contexto)

def nosotros(request):
    try:
        admin_user = User.objects.get(email='admin@admin.com')
        admin_profile = AdminProfile.objects.filter(user=admin_user).first()
    except User.DoesNotExist:
        admin_user = None
        admin_profile = None

    contexto = {
        'admin_user': admin_user,
        'admin_profile': admin_profile,
    }
    return render(request, 'vistas/nosotros.html', contexto)
