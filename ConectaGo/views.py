# Removed duplicate imports and organized them
import json
import requests
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, F, Avg
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.conf import settings
from .forms import (
    LoginForm,
    ClientRegistrationForm,
    ProfessionalRegistrationForm,
    AdminProfileForm,
    ClientProfileForm,
    ProfessionalProfileForm,
)
from ConectaGo.models import ProfessionalProfile, ClientProfile, AdminProfile, Appointment, Review, Report, Notification
from django.utils import timezone
from ConectaGo.forms import ReportForm
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt


def home(request):
    profesion = request.GET.get('profesion', '').strip()
    comuna_seleccionada = request.GET.get('ubicacion', '').strip()

    profesionales = ProfessionalProfile.objects.all()

    # Obtener todas las ubicaciones distintas
    ubicaciones = ProfessionalProfile.objects.values_list('ubicacion', flat=True).distinct()

    # Extraer comunas de las ubicaciones (penúltima parte al separar por comas)
    regiones_conocidas = {
        "Región Metropolitana",
        "Región de Valparaíso",
        "Región del Biobío",
        "Región de La Araucanía",
        "Región de Los Lagos",
        "Región de Coquimbo",
        "Región de Antofagasta",
        "Región de Atacama",
        "Región de Magallanes",
        "Región de O'Higgins",
        "Región de Maule",
        "Región de Ñuble",
        "Región de Los Ríos",
        "Región de Arica y Parinacota",
        "Región de Tarapacá",
        "Región de Aysén",
        "Región de Libertador General Bernardo O'Higgins"
    }
    import re
    comunas = set()
    for ubic in ubicaciones:
        partes = [p.strip() for p in ubic.split(',')]
        # Eliminar "Chile" y regiones conocidas
        partes_filtradas = [p for p in partes if p.lower() != 'chile' and p not in regiones_conocidas]
        comuna = None
        ciudad = None
        region = None
        # Buscar la primera parte desde la derecha que no contenga dígitos
        for parte in reversed(partes_filtradas):
            # Limpiar códigos numéricos al inicio
            parte_limpia = re.sub(r'^\d+\s*', '', parte)
            if parte_limpia:
                comuna = parte_limpia
                break
        # Si no se encontró comuna limpia, usar la última parte filtrada limpia
        if not comuna and partes_filtradas:
            comuna = re.sub(r'^\d+\s*', '', partes_filtradas[-1])
        # Si no hay comuna, usar ciudad o región
        if comuna:
            comunas.add(comuna)
        elif len(partes) >= 2:
            region = partes[-2]
            if region not in regiones_conocidas:
                comunas.add(region)
    comunas = sorted(comunas)

    # Filtrar profesionales por comuna seleccionada si no es "Todas las ubicaciones"
    if comuna_seleccionada and comuna_seleccionada != 'Todas las ubicaciones':
        profesionales = profesionales.filter(ubicacion__icontains=comuna_seleccionada)

    if profesion and profesion != 'Todas las profesiones':
        profesionales = profesionales.filter(especialidad__icontains=profesion)

    profesiones = ProfessionalProfile.objects.values_list('especialidad', flat=True).distinct()

    # --- NUEVO: Generar lista de ubicaciones para el mapa ---
    profesionales_ubicaciones = []
    for prof in profesionales:
        if prof.latitud is not None and prof.longitud is not None:
            profesionales_ubicaciones.append({
                'nombre': f"{prof.nombre} {prof.apellido}",
                'especialidad': prof.especialidad,
                'latitud': prof.latitud,
                'longitud': prof.longitud,
                'url': reverse('ConectaGo:public_professional_profile', args=[prof.user.username])
            })

    # Anotar el promedio de valoraciones para cada profesional
    profesionales = profesionales.annotate(avg_rating=Avg('reviews__rating'))

    contexto = {
        'profesionales': profesionales,
        'ubicaciones': ['Todas las ubicaciones'] + comunas,
        'profesion': profesion,
        'ubicacion': comuna_seleccionada,
        'profesiones': ['Todas las profesiones'] + list(profesiones),
        'profesionales_ubicaciones': json.dumps(profesionales_ubicaciones),
        'google_maps_api_key': 'AIzaSyCo9E96ubTQ8C-4KtQ1kZUXBqkJwWH5seQ',
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
            ubicacion = form.cleaned_data.get('ubicacion', '')
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
                        especialidad='',
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

    import os
    import time

    photo_timestamp = ''
    if professional_profile and professional_profile.foto:
        try:
            photo_path = professional_profile.foto.path
            photo_timestamp = str(int(os.path.getmtime(photo_path)))
        except Exception:
            photo_timestamp = ''

    contexto = {
        'form': form,
        'professional_profile': professional_profile,
        'specialties': specialties,
        'photo_timestamp': photo_timestamp,
    }
    return render(request, 'vistas/professional_profile_edit.html', contexto)

def login_view(request):
    test_users = {
        'cliente 1': {'email': 'cli1@mail.com', 'password': 'cli1234'},
        'cliente 2': {'email': 'cli2@mail.com', 'password': 'cli1234'},
        'cliente 3': {'email': 'cli3@mail.com', 'password': 'cli1234'},
        'cliente 4': {'email': 'cli4@mail.com', 'password': 'cli1234'},
        'cliente 5': {'email': 'cli5@mail.com', 'password': 'cli1234'},
        'profesional 1': {'email': 'pro1@mail.com', 'password': 'pro1234'},
        'profesional 2': {'email': 'pro2@mail.com', 'password': 'pro1234'},
        'profesional 3': {'email': 'pro3@mail.com', 'password': 'pro1234'},
        'profesional 4': {'email': 'pro4@mail.com', 'password': 'pro1234'},
        'profesional 5': {'email': 'pro5@mail.com', 'password': 'pro1234'},
        'administrador': {'email': 'admin@admin.com', 'password': 'admin123'},
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

from ConectaGo.models import ChatRoom, ChatMessage

@login_required
@staff_member_required
def admin_certification_management(request):
    from django.core.mail import send_mail
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('ConectaGo:home')

    professionals = ProfessionalProfile.objects.all().order_by('nombre', 'apellido')

    if request.method == 'POST':
        prof_id = request.POST.get('professional_id')
        action = request.POST.get('action')
        rejection_message = request.POST.get('rejection_message', '').strip()

        try:
            professional = ProfessionalProfile.objects.get(id=prof_id)
        except ProfessionalProfile.DoesNotExist:
            messages.error(request, "Profesional no encontrado.")
            return redirect('ConectaGo:admin_certification_management')

        if action == 'accept':
            professional.certification_status = 'accepted'
            professional.certification_rejection_message = ''
            professional.save()
            messages.success(request, f"Certificación de {professional.nombre} {professional.apellido} aceptada.")

            # Send automatic chat message about acceptance
            admin_user = request.user
            # Find or create chatroom between admin and professional
            chatroom = ChatRoom.objects.filter(participants=admin_user).filter(participants=professional.user).first()
            if not chatroom:
                chatroom = ChatRoom.objects.create()
                chatroom.participants.add(admin_user, professional.user)
                chatroom.save()
            # Create chat message
            ChatMessage.objects.create(
                chatroom=chatroom,
                sender=admin_user,
                content=f"Su certificación ha sido aceptada. ¡Felicidades, {professional.nombre}!"
            )

        elif action == 'reject':
            if not rejection_message:
                messages.error(request, "Debe proporcionar un mensaje de rechazo.")
                return redirect('ConectaGo:admin_certification_management')
            professional.certification_status = 'rejected'
            professional.certification_rejection_message = rejection_message
            professional.save()
            # Remove adding rejection message to Django messages to avoid login message
            # messages.success(request, f"Certificación de {professional.nombre} {professional.apellido} rechazada y notificación enviada.")

            # Create in-app notification for professional with full rejection message
            Notification.objects.create(
                user=professional.user,
                message=f"Certificación de {professional.nombre} {professional.apellido} rechazada. Motivo: {rejection_message}",
                read=False,
                created_at=timezone.now()
            )
            messages.success(request, f"Certificación de {professional.nombre} {professional.apellido} rechazada.")

            # Send notification email to professional
            subject = "Su certificación ha sido rechazada"
            message = f"Hola {professional.nombre},\n\nSu certificación ha sido rechazada por el siguiente motivo:\n\n{rejection_message}\n\nPor favor, revise y vuelva a subir su certificación.\n\nSaludos,\nEquipo Conecta.go"
            recipient_list = [professional.user.email]
            send_mail(subject, message, None, recipient_list, fail_silently=True)

            # Send automatic chat message about rejection
            admin_user = request.user
            # Find or create chatroom between admin and professional
            chatroom = ChatRoom.objects.filter(participants=admin_user).filter(participants=professional.user).first()
            if not chatroom:
                chatroom = ChatRoom.objects.create()
                chatroom.participants.add(admin_user, professional.user)
                chatroom.save()
            # Create chat message
            ChatMessage.objects.create(
                chatroom=chatroom,
                sender=admin_user,
                content=f"Su certificación ha sido rechazada. Motivo: {rejection_message}"
            )
        else:
            messages.error(request, "Acción no válida.")

        return redirect('ConectaGo:admin_certification_management')

    contexto = {
        'professionals': professionals,
    }
    return render(request, 'vistas/admin_certification_management.html', contexto)

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


from django.http import Http404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from ConectaGo.models import ProfessionalProfile, Appointment
from ConectaGo.forms import ProfessionalProfileForm
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth import logout
from django.shortcuts import redirect

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib import messages

@login_required
def metodo_de_pago(request, appointment_id):
    from ConectaGo.models import Appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        messages.error(request, 'Cita no encontrada.')
        return redirect('ConectaGo:cliente_citas')

    # Get the price of the appointment's service
    price = None
    if appointment.service:
        price = appointment.service.price  # Assuming service has a price field

    # Render a payment method page with price and options
    context = {
        'appointment': appointment,
        'price': price,
    }
    return render(request, 'vistas/metodo_de_pago.html', context)

@login_required
def pago_online(request, appointment_id):
    # Placeholder for online payment processing
    messages.success(request, "Pago online procesado correctamente (simulado).")
    return redirect('ConectaGo:cliente_citas')

@login_required
def pago_efectivo(request, appointment_id):
    # Placeholder for cash payment processing
    messages.success(request, "Pago en efectivo registrado correctamente (simulado).")
    return redirect('ConectaGo:cliente_citas')

@login_required
def delete_chatroom_view(request, chatroom_id):
    user = request.user
    from ConectaGo.models import ChatRoom

    chatroom = get_object_or_404(ChatRoom, id=chatroom_id)

    # Check if user is a participant of the chatroom
    if user not in chatroom.participants.all():
        return HttpResponseForbidden("No tienes permiso para eliminar este chat.")

    # Delete the chatroom
    chatroom.delete()

    # Redirect to chat list page
    return redirect('ConectaGo:chat')

@csrf_exempt
@login_required
def send_message_view(request):
    if request.method == 'POST':
        user = request.user
        chatroom_id = request.POST.get('chatroom_id')
        message_content = request.POST.get('message', '').strip()

        if not chatroom_id or not message_content:
            messages.error(request, 'El mensaje no puede estar vacío.')
            return redirect('ConectaGo:chat')

        from ConectaGo.models import ChatRoom, ChatMessage
        try:
            chatroom = ChatRoom.objects.get(id=chatroom_id)
        except ChatRoom.DoesNotExist:
            messages.error(request, 'Chat no encontrado.')
            return redirect('ConectaGo:chat')

        if user not in chatroom.participants.all():
            return HttpResponseForbidden('No tienes permiso para enviar mensajes en este chat.')

        # Create new message
        ChatMessage.objects.create(
            chatroom=chatroom,
            sender=user,
            content=message_content
        )

        # Redirect back to chat view with selected chatroom
        return redirect(f"{reverse('ConectaGo:chat')}?chat_id={chatroom_id}")
    else:
        return HttpResponseForbidden('Método no permitido.')

@login_required
def chat_view(request):
    user = request.user
    has_access = False
    # Check if user has adminprofile, professionalprofile or clientprofile
    if hasattr(user, 'adminprofile') or hasattr(user, 'professionalprofile') or hasattr(user, 'clientprofile'):
        has_access = True

    if not has_access:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    # Get chat rooms for user
    chatrooms = user.chatrooms.all().order_by('-created_at')

    # Get selected chatroom id from query param
    chat_id = request.GET.get('chat_id')
    username = request.GET.get('username')
    messages = []
    selected_chatroom = None

    # If username param is provided, find or create chatroom with that user
    if username:
        from django.contrib.auth.models import User as AuthUser
        from ConectaGo.models import ChatRoom

        try:
            other_user = AuthUser.objects.get(username=username)
            # Check if chatroom exists between user and other_user
            chatroom = ChatRoom.objects.filter(participants=user).filter(participants=other_user).first()
            if not chatroom:
                # Create new chatroom
                chatroom = ChatRoom.objects.create()
                chatroom.participants.add(user, other_user)
                chatroom.save()
            selected_chatroom = chatroom
        except AuthUser.DoesNotExist:
            selected_chatroom = None

    # If no selected chatroom from username, fallback to chat_id param
    if not selected_chatroom and chat_id:
        try:
            selected_chatroom = chatrooms.get(id=chat_id)
        except Exception:
            selected_chatroom = None

    # If still no selected chatroom, pick first chatroom if exists
    if not selected_chatroom and chatrooms.exists():
        selected_chatroom = chatrooms.first()

    if selected_chatroom:
        messages = selected_chatroom.messages.order_by('timestamp')

    # Determine other participant's email for display
    other_participant_email = None
    if selected_chatroom:
        other_participants = selected_chatroom.participants.exclude(id=user.id)
        if other_participants.exists():
            other_participant_email = other_participants.first().email

    context = {
        'chatrooms': chatrooms,
        'messages': messages,
        'selected_chatroom': selected_chatroom,
        'other_participant_email': other_participant_email,
    }

    return render(request, 'vistas/chat.html', context)

@login_required
def reschedule_appointment_view(request, appointment_id):
    from ConectaGo.models import Appointment, ChatRoom, ChatMessage
    import datetime
    import logging

    if request.method == 'POST':
        user = request.user
        reason = request.POST.get('reschedule_reason', '').strip()
        if not reason:
            messages.error(request, 'Debe ingresar un motivo para reagendar.')
            return redirect('ConectaGo:cliente_citas')

        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            messages.error(request, 'Cita no encontrada.')
            return redirect('ConectaGo:cliente_citas')

        # Check if the appointment belongs to the user (client)
        if appointment.client.user != user:
            messages.error(request, 'No tiene permiso para reagendar esta cita.')
            return redirect('ConectaGo:cliente_citas')

        # Cancel the appointment (or delete)
        appointment.status = 'cancelled'
        appointment.cancel_reason = f"Reagendado: {reason}"
        appointment.save()

        # Send chat message to the other user
        other_user = appointment.professional.user if appointment.client.user == user else appointment.client.user

        if other_user:
            # Find or create chatroom between users
            chatroom = ChatRoom.objects.filter(participants=user).filter(participants=other_user).first()
            if not chatroom:
                chatroom = ChatRoom.objects.create()
                chatroom.participants.add(user, other_user)
                chatroom.save()

        message_content = f"La cita ha sido reagendada. Motivo: {reason}. Por favor, seleccione una nueva fecha y hora."
        ChatMessage.objects.create(
            chatroom=chatroom,
            sender=user,
            content=message_content
        )

        messages.success(request, 'Cita reagendada correctamente. Por favor, seleccione una nueva fecha y hora.')

        # Redirect to professional schedule page to select new appointment
        professional_username = appointment.professional.user.username
        return redirect('ConectaGo:professional_schedule', username=professional_username)
    else:
        return HttpResponseForbidden('Método no permitido.')

@login_required
def borrar_cuenta_profesional_view(request):
    user = request.user
    if not hasattr(user, 'professionalprofile'):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('ConectaGo:home')

    if request.method == 'POST':
        confirm_text = request.POST.get('confirm_text', '').strip()
        if confirm_text != 'ELIMINAR':
            messages.error(request, 'Debes escribir "ELIMINAR" en mayúsculas para confirmar.')
            return redirect('ConectaGo:borrar_cuenta_profesional')

        # Delete related professional photos first to avoid FK constraint error
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM ConectaGo_professionalphoto WHERE professional_id = %s", [user.professionalprofile.id])
        except Exception:
            pass

        # Delete professional profile and user with error handling for FK constraint
        try:
            user.professionalprofile.delete()
            logout(request)
            user.delete()
            messages.success(request, 'Tu cuenta ha sido borrada correctamente.')
            return redirect('ConectaGo:home')
        except Exception as e:
            import logging
            logging.error(f"Error deleting professional profile or user: {e}", exc_info=True)
            messages.error(request, f"No se pudo eliminar la cuenta debido a una restricción de clave foránea: {e}")
            return redirect('ConectaGo:borrar_cuenta_profesional')

    return render(request, 'vistas/borrar_cuenta.html', {'user_type': 'profesional'})

@login_required
@staff_member_required
def delete_review_view(request, review_id):
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para eliminar opiniones.")
        return redirect('ConectaGo:reportes')

    review = get_object_or_404(Review, id=review_id)
    # professional_profile = review.professional  # Ya no se usa para redirección

    if request.method == 'POST':
        review.delete()
        messages.success(request, "Opinión eliminada correctamente.")
        return redirect('ConectaGo:reportes')

    contexto = {
        'review': review,
    }
    return render(request, 'vistas/confirm_delete_review.html', contexto)
    user = request.user
    if not hasattr(user, 'professionalprofile'):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('ConectaGo:home')

    if request.method == 'POST':
        confirm_text = request.POST.get('confirm_text', '').strip()
        if confirm_text != 'ELIMINAR':
            messages.error(request, 'Debes escribir "ELIMINAR" en mayúsculas para confirmar.')
            return redirect('ConectaGo:borrar_cuenta_profesional')

        # Delete professional profile and user
        try:
            user.professionalprofile.delete()
        except Exception:
            pass
        logout(request)
        user.delete()
        messages.success(request, 'Tu cuenta ha sido borrada correctamente.')
        return redirect('ConectaGo:home')

    return render(request, 'vistas/borrar_cuenta.html', {'user_type': 'profesional'})

@login_required
def borrar_cuenta_cliente_view(request):
    user = request.user
    if not hasattr(user, 'clientprofile'):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('ConectaGo:home')

    if request.method == 'POST':
        confirm_text = request.POST.get('confirm_text', '').strip()
        if confirm_text != 'ELIMINAR':
            messages.error(request, 'Debes escribir "ELIMINAR" en mayúsculas para confirmar.')
            return redirect('ConectaGo:borrar_cuenta_cliente')

        # Delete client profile and user
        try:
            user.clientprofile.delete()
        except Exception:
            pass
        logout(request)
        user.delete()
        messages.success(request, 'Tu cuenta ha sido borrada correctamente.')
        return redirect('ConectaGo:home')

    return render(request, 'vistas/borrar_cuenta.html', {'user_type': 'cliente'})

@login_required
def admin_analisis_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    # Get filter parameters from GET
    ubicacion_filter = request.GET.get('ubicacion', '')
    especialidad_filter = request.GET.get('especialidad', '')

    # Get distinct locations and specialties for filter dropdowns
    ubicaciones = ProfessionalProfile.objects.values_list('ubicacion', flat=True).distinct().order_by('ubicacion')
    especialidades = ProfessionalProfile.objects.values_list('especialidad', flat=True).distinct().order_by('especialidad')

    # Base queryset of professionals
    profesionales = ProfessionalProfile.objects.all()

    # Apply filters if provided
    if ubicacion_filter:
        profesionales = profesionales.filter(ubicacion__icontains=ubicacion_filter)
    if especialidad_filter:
        profesionales = profesionales.filter(especialidad__icontains=especialidad_filter)

    # Annotate with count of appointments
    profesionales = profesionales.annotate(cantidad_agendamientos=Count('appointments'))

    contexto = {
        'profesionales': profesionales,
        'ubicaciones': ubicaciones,
        'especialidades': especialidades,
        'ubicacion_filter': ubicacion_filter,
        'especialidad_filter': especialidad_filter,
    }
    return render(request, 'vistas/admin_analisis.html', contexto)

from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

@login_required
def admin_analisis_pdf_view(request):
    import logging
    logging.info("admin_analisis_pdf_view called")
    try:
        if not request.user.is_superuser:
            logging.warning("User is not superuser, access denied")
            return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

        ubicacion_filter = request.GET.get('ubicacion', '')
        especialidad_filter = request.GET.get('especialidad', '')
        logging.info(f"Filters received - ubicacion: {ubicacion_filter}, especialidad: {especialidad_filter}")

        profesionales = ProfessionalProfile.objects.all()
        if ubicacion_filter:
            profesionales = profesionales.filter(ubicacion__icontains=ubicacion_filter)
        if especialidad_filter:
            profesionales = profesionales.filter(especialidad__icontains=especialidad_filter)

        profesionales = profesionales.annotate(cantidad_agendamientos=Count('appointments'))[:100]  # Limit to 100 for testing

        # Create PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Reporte de Datos Generales - Conecta.go")

        p.setFont("Helvetica", 12)
        y = height - 80
        p.drawString(50, y, f"Filtro Ubicación: {ubicacion_filter or 'Todas'}")
        y -= 20
        p.drawString(50, y, f"Filtro Especialidad: {especialidad_filter or 'Todas'}")
        y -= 40

        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.wordWrap = 'CJK'  # Enable wrapping for CJK and long words

        # Prepare table data
        data = []
        # Header row
        data.append([
            Paragraph("<b>Ubicación</b>", normal_style),
            Paragraph("<b>Especialidad</b>", normal_style),
            Paragraph("<b>Cantidad de Agendamientos</b>", normal_style)
        ])

        # Data rows
        for prof in profesionales:
            data.append([
                Paragraph(prof.ubicacion or "", normal_style),
                Paragraph(prof.especialidad or "", normal_style),
                str(prof.cantidad_agendamientos)
            ])

        # Define column widths
        col_widths = [250, 200, 100]

        # Create table
        table = Table(data, colWidths=col_widths)

        # Add style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ])
        table.setStyle(style)

        # Calculate table height and position
        table_width, table_height = table.wrap(0, 0)
        x = 50
        current_y = y

        # Check if table fits on current page, else create new page
        if current_y - table_height < 50:
            p.showPage()
            current_y = height - 50

        # Draw table
        table.wrapOn(p, width, height)
        table.drawOn(p, x, current_y - table_height)

        p.showPage()
        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_datos_generales.pdf"'
        logging.info("PDF generated successfully, returning response")
        return response
    except Exception as e:
        logging.error(f"Error generating PDF report: {e}", exc_info=True)
        return HttpResponse("Error al generar el reporte PDF. Por favor, inténtelo de nuevo más tarde.", status=500)

@login_required
def report_review(request, review_id):
    user = request.user
    try:
        professional_profile = user.professionalprofile
    except ProfessionalProfile.DoesNotExist:
        messages.error(request, "No tienes permiso para reportar opiniones.")
        return HttpResponseRedirect(reverse('ConectaGo:mi_perfil_profesional'))

    review = get_object_or_404(Review, id=review_id)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            justification = form.cleaned_data['justification']
            Report.objects.create(
                review=review,
                reporter=professional_profile,
                justification=justification,
                status='pending'
            )
            messages.success(request, "Reporte enviado correctamente.")
            return HttpResponseRedirect(reverse('ConectaGo:mi_perfil_profesional'))
    else:
        form = ReportForm()

    contexto = {
        'form': form,
        'review': review,
    }
    return render(request, 'vistas/report_review.html', contexto)

@login_required
@staff_member_required
def report_list(request):
    reports = Report.objects.select_related('review', 'reporter', 'review__professional').order_by('-created_at')
    contexto = {
        'reports': reports,
    }
    return render(request, 'vistas/reportes.html', contexto)

def mi_perfil_profesional_view(request):
    user = request.user

    try:
        professional_profile = ProfessionalProfile.objects.get(user=user)
    except ProfessionalProfile.DoesNotExist:
        raise Http404("Perfil profesional no encontrado")

    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    from ConectaGo.models import Review, Reply, ProfessionalPhoto
    if request.method == 'POST':
        # Manejar guardado de respuesta a comentario
        if 'reply_text' in request.POST and 'review_id' in request.POST:
            reply_text = request.POST.get('reply_text', '').strip()
            review_id = request.POST.get('review_id')
            if reply_text and review_id:
                try:
                    review = Review.objects.get(id=review_id, professional=professional_profile)
                    # Crear respuesta
                    Reply.objects.create(
                        review=review,
                        professional=professional_profile,
                        texto=reply_text
                    )
                    messages.success(request, 'Respuesta guardada correctamente')
                except Review.DoesNotExist:
                    messages.error(request, 'Comentario no encontrado o no pertenece a este profesional')
            else:
                messages.error(request, 'Debe ingresar texto para la respuesta')
            return redirect('ConectaGo:mi_perfil_profesional')

        # Manejar subida de foto con descripción
        if 'photo' in request.FILES:
            if professional_profile.user != user:
                messages.error(request, 'No tiene permiso para cambiar esta foto.')
                return redirect('ConectaGo:mi_perfil_profesional')
            photo = request.FILES['photo']
            description = request.POST.get('description', '').strip()
            ProfessionalPhoto.objects.create(
                professional=professional_profile,
                photo=photo,
                description=description
            )
            messages.success(request, 'Foto subida correctamente')
            return redirect('ConectaGo:mi_perfil_profesional')

        # Manejar cambio de foto de perfil de forma independiente
        if 'foto' in request.FILES:
            if professional_profile.user != user:
                messages.error(request, 'No tiene permiso para cambiar esta foto de perfil.')
                return redirect('ConectaGo:mi_perfil_profesional')
            foto = request.FILES['foto']
            professional_profile.foto = foto
            professional_profile.save()
            messages.success(request, 'Foto de perfil actualizada correctamente')
            return redirect('ConectaGo:mi_perfil_profesional')

        # Check if this is a partial update for descripcion only
        if 'descripcion' in request.POST and len(request.POST) == 2:  # csrf token + descripcion
            descripcion = request.POST.get('descripcion', '').strip()
            professional_profile.descripcion = descripcion
            professional_profile.save()
            messages.success(request, 'Descripción actualizada correctamente')
            return redirect('ConectaGo:mi_perfil_profesional')

        # Check if this is a partial update for ubicacion only
        if 'ubicacion' in request.POST and len(request.POST) in (2, 4):  # csrf token + ubicacion (+ latitud/longitud)
            ubicacion = request.POST.get('ubicacion', '').strip()
            latitud = request.POST.get('latitud', None)
            longitud = request.POST.get('longitud', None)
            professional_profile.ubicacion = ubicacion
            if latitud is not None and latitud != '':
                try:
                    professional_profile.latitud = float(latitud)
                except ValueError:
                    professional_profile.latitud = None
            if longitud is not None and longitud != '':
                try:
                    professional_profile.longitud = float(longitud)
                except ValueError:
                    professional_profile.longitud = None
            professional_profile.save()
            messages.success(request, 'Ubicación actualizada correctamente')
            return redirect('ConectaGo:mi_perfil_profesional')

        # Check if this is a partial update for schedule only
        if any(key.endswith('_start') or key.endswith('_end') or key.endswith('_closed') for key in request.POST.keys()):
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
            return redirect('ConectaGo:mi_perfil_profesional')

        # Check if this is a partial update for prices
        if 'price_description' in request.POST and 'price_value' in request.POST:
            # Clear existing prices and add new ones from the form data
            professional_profile.prices.all().delete()
            descriptions = request.POST.getlist('price_description')
            values = request.POST.getlist('price_value')
            for desc, val in zip(descriptions, values):
                desc = desc.strip()
                try:
                    val_float = float(val)
                except (ValueError, TypeError):
                    val_float = None
                if desc and val_float is not None:
                    professional_profile.prices.create(description=desc, price=val_float)
            messages.success(request, 'Precios actualizados correctamente')
            return redirect('ConectaGo:mi_perfil_profesional')

        # Otherwise, handle full form update
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
            return redirect('ConectaGo:mi_perfil_profesional')
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

    schedule = professional_profile.schedule if professional_profile.schedule else {}
    prices_qs = professional_profile.prices.all()
    # Convert prices to list of dicts with string price for template input compatibility
    prices = []
    for p in prices_qs:
        prices.append({
            'id': p.id,
            'description': p.description,
            'price': format(p.price, 'f'),  # Convert Decimal to string with dot decimal
        })

    # Flatten schedule dictionary for template
    schedule_flat = {}
    for day in days:
        day_lower = day.lower()
        day_schedule = schedule.get(day, {})
        schedule_flat[f"{day_lower}_start"] = day_schedule.get('start', '')
        schedule_flat[f"{day_lower}_end"] = day_schedule.get('end', '')
        schedule_flat[f"{day_lower}_closed"] = day_schedule.get('closed', False)

    # Cargar reviews con sus respuestas
    reviews = Review.objects.filter(professional=professional_profile).order_by('-fecha').prefetch_related('replies')

    # Calcular conteos para filtros de opiniones
    total_reviews = reviews.count()
    positive_reviews_count = reviews.filter(rating__gte=4).count()
    neutral_reviews_count = reviews.filter(rating=3).count()
    negative_reviews_count = reviews.filter(rating__lte=2).count()

    contexto = {
        'form': form,
        'professional_profile': professional_profile,
        'schedule': schedule,
        'schedule_flat': schedule_flat,
        'days': days,
        'prices': prices,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'positive_reviews_count': positive_reviews_count,
        'neutral_reviews_count': neutral_reviews_count,
        'negative_reviews_count': negative_reviews_count,
    }
    return render(request, 'vistas/mi_perfil_profesional.html', contexto)

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.urls import reverse

@login_required
def delete_user_view(request, user_type, user_id):
    if request.method == 'POST':
        # Perform deletion
        try:
            user = get_object_or_404(User, id=user_id)
            if user.email.lower() == 'admin@admin.com':
                messages.error(request, 'No se puede eliminar al usuario administrador.')
                return redirect('ConectaGo:admin_user_list')

            # Delete related profiles explicitly to avoid FK constraint errors
            ClientProfile.objects.filter(user=user).delete()
            ProfessionalProfile.objects.filter(user=user).delete()

            # Now delete the user
            user.delete()

            messages.success(request, 'Usuario eliminado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar usuario: {str(e)}')
        return redirect('ConectaGo:admin_user_list')
    else:
        # GET request: show confirmation inline in admin_user_list
        clientes = ClientProfile.objects.exclude(user__email__iexact='admin@admin.com')
        profesionales = ProfessionalProfile.objects.exclude(user__email__iexact='admin@admin.com')
        user_to_delete = None
        try:
            user_to_delete = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado para confirmar eliminación.')
        contexto = {
            'clientes': clientes,
            'profesionales': profesionales,
            'confirm_delete': True,
            'delete_user_type': user_type,
            'delete_user_id': user_id,
            'delete_user_email': user_to_delete.email if user_to_delete else '',
            'delete_user_name': f"{user_to_delete.first_name} {user_to_delete.last_name}" if user_to_delete else '',
        }
        return render(request, 'vistas/admin_user_list.html', contexto)

def update_professional_profile(user, form, professional_profile=None):
    telefono = form.cleaned_data.get('telefono')
    if telefono and not telefono.startswith("+56 9"):
        telefono = "+56 9" + telefono

    nombre = form.cleaned_data['nombre']
    apellido = form.cleaned_data['apellido']
    especialidad = form.cleaned_data['especialidad']
    nombre_certificado = form.cleaned_data.get('nombre_certificado')
    entidad_emisora = form.cleaned_data.get('entidad_emisora')
    fecha_emision = form.cleaned_data.get('fecha_emision')
    archivo_pdf = form.cleaned_data.get('archivo_pdf')
    email = form.cleaned_data['email']
    password = form.cleaned_data['password']
    foto = form.cleaned_data.get('foto')
    calendly_event_uri = form.cleaned_data.get('calendly_event_uri')

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

    # Update or create professional profile
    if professional_profile:
        if foto:
            professional_profile.foto = foto
        professional_profile.nombre = nombre
        professional_profile.apellido = apellido
        professional_profile.especialidad = especialidad
        professional_profile.telefono = telefono
        professional_profile.nombre_certificado = nombre_certificado
        professional_profile.entidad_emisora = entidad_emisora
        professional_profile.fecha_emision = fecha_emision
        if archivo_pdf:
            professional_profile.archivo_pdf = archivo_pdf
        professional_profile.calendly_event_uri = calendly_event_uri
        professional_profile.save()
    else:
        professional_profile = ProfessionalProfile.objects.create(
            user=user,
            nombre=nombre,
            apellido=apellido,
            especialidad=especialidad,
            telefono=telefono,
            nombre_certificado=nombre_certificado,
            entidad_emisora=entidad_emisora,
            fecha_emision=fecha_emision,
            archivo_pdf=archivo_pdf,
            foto=foto,
            calendly_event_uri=calendly_event_uri,
        )
    return professional_profile

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
            professional_profile = update_professional_profile(user, form, professional_profile)
            messages.success(request, 'Datos actualizados correctamente')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        initial_data = {
            'nombre': user.first_name or '',
            'apellido': user.last_name or '',
            'especialidad': professional_profile.especialidad if professional_profile else '',
            'telefono': professional_profile.telefono if professional_profile else '',
            'nombre_certificado': professional_profile.nombre_certificado if professional_profile else '',
            'entidad_emisora': professional_profile.entidad_emisora if professional_profile else '',
            'fecha_emision': professional_profile.fecha_emision if professional_profile else None,
            'calendly_event_uri': professional_profile.calendly_event_uri if professional_profile else '',
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

import datetime
import logging

def public_professional_profile_view(request, username):
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

    # Obtener precios relacionados
    precios = professional_profile.prices.all()

    # Format prices with thousands separator and decimal comma
    from django.utils.formats import number_format
    formatted_precios = []
    for price in precios:
        # Format price.price as string with 0 decimals, thousands separator, and decimal comma
        formatted_price = number_format(price.price, decimal_pos=0, use_l10n=True, force_grouping=True)
        # number_format uses locale decimal separator, but to ensure comma, replace dot with comma
        formatted_price = formatted_price.replace('.', ',')
        formatted_precios.append({
            'description': price.description,
            'formatted_price': formatted_price,
        })

    has_client_profile = False
    client_nombre = None
    client_apellido = None
    if request.user.is_authenticated:
        try:
            client_profile = request.user.clientprofile
            has_client_profile = True
            client_nombre = client_profile.nombre
            client_apellido = client_profile.apellido
        except Exception:
            has_client_profile = False

    from ConectaGo.models import Review, Reply, ProfessionalPhoto
    if request.method == 'POST' and request.POST.get('review_submit'):
        if not has_client_profile:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Debes tener un perfil de cliente para dejar una opinión.'}, status=400)
            messages.error(request, 'Debes tener un perfil de cliente para dejar una opinión.')
            return redirect(request.path)
        # Validar consentimiento
        consent = request.POST.get('consent')
        if consent != 'on':
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Debes consentir el tratamiento de datos para dejar una opinión.'}, status=400)
            messages.error(request, 'Debes consentir el tratamiento de datos para dejar una opinión.')
            return redirect(request.path)
        rating = int(request.POST.get('rating', 0))
        opinion = request.POST.get('opinion', '').strip()
        likes = request.POST.getlist('likes')
        improve = request.POST.getlist('improve')
        if rating < 1 or rating > 5 or len(opinion) < 10:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({'error': 'Por favor completa todos los campos obligatorios.'}, status=400)
            messages.error(request, 'Por favor completa todos los campos obligatorios.')
            return redirect(request.path)
        review = Review.objects.create(
            professional=professional_profile,
            client=request.user.clientprofile,
            nombre=f"{client_nombre} {client_apellido}",
            rating=rating,
            opinion=opinion,
            likes=likes,
            improve=improve
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'nombre': review.nombre,
                'rating': review.rating,
                'opinion': review.opinion,
                'likes': review.likes or [],
                'improve': review.improve or [],
                'foto_url': review.client.foto_url if review.client else '',
            })
        messages.success(request, '¡Gracias por tu opinión!')
        return redirect(request.path)

    reviews = Review.objects.filter(professional=professional_profile).order_by('-fecha').prefetch_related('replies')

    # Calcular promedio de estrellas y total de opiniones
    avg_rating = 0
    total_reviews = reviews.count()
    if total_reviews > 0:
        avg_rating = round(sum([r.rating for r in reviews]) / total_reviews, 1)

    # Calcular conteos para filtros de opiniones
    positive_reviews_count = reviews.filter(rating__gte=4).count()
    neutral_reviews_count = reviews.filter(rating=3).count()
    negative_reviews_count = reviews.filter(rating__lte=2).count()

    # Get professional photos
    photos = ProfessionalPhoto.objects.filter(professional=professional_profile).order_by('-created_at')

    contexto = {
        'professional_profile': professional_profile,
        'google_maps_api_key': 'AIzaSyCo9E96ubTQ8C-4KtQ1kZUXBqkJwWH5seQ',  # Reemplaza con tu clave API real o configúrala dinámicamente
        'comuna': comuna,
        'ciudad': ciudad,
        'precios': formatted_precios,
        'has_client_profile': has_client_profile,
        'client_nombre': client_nombre,
        'client_apellido': client_apellido,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'positive_reviews_count': positive_reviews_count,
        'neutral_reviews_count': neutral_reviews_count,
        'negative_reviews_count': negative_reviews_count,
        'photos': photos,
    }
    return render(request, 'vistas/public_professional_profile.html', contexto)

@login_required
def professional_schedule_view(request, username):
    try:
        try:
            user = User.objects.get(username=username)
            professional_profile = ProfessionalProfile.objects.get(user=user)
        except (User.DoesNotExist, ProfessionalProfile.DoesNotExist):
            logging.error(f"Perfil profesional no encontrado para username: {username}")
            raise Http404("Perfil profesional no encontrado")

        # Obtener día seleccionado desde GET, formato 'YYYY-MM-DD'
        day_str = request.GET.get('day')
        if day_str:
            try:
                selected_day = datetime.datetime.strptime(day_str, '%Y-%m-%d').date()
            except ValueError:
                selected_day = datetime.date.today()
        else:
            selected_day = datetime.date.today()

        schedule = professional_profile.schedule if professional_profile.schedule else {}

        # Definir rangos horarios para mañana, tarde y noche en formato HH:MM
        morning_hours = [f"{h:02d}:00" for h in range(7, 12)]  # 08:00 a 11:00
        afternoon_hours = [f"{h:02d}:00" for h in range(12, 18)]  # 12:00 a 17:00
        night_hours = [f"{h:02d}:00" for h in range(18, 23)]  # 18:00 a 21:00

        # Función para verificar si una hora está disponible en el schedule para el día seleccionado
        def is_hour_available(hour_str, schedule, day_name):
            day_schedule = schedule.get(day_name, {})
            if day_schedule.get('closed'):
                return False
            start = day_schedule.get('start')
            end = day_schedule.get('end')
            if not start or not end:
                return False
            # Convertir a datetime.time para comparación
            fmt = "%H:%M"
            from datetime import datetime as dt
            try:
                hour_time = dt.strptime(hour_str, fmt).time()
                start_time = dt.strptime(start, fmt).time()
                end_time = dt.strptime(end, fmt).time()
                return start_time <= hour_time < end_time
            except Exception as e:
                logging.error(f"Error parsing time: {e}")
                return False

        # Obtener nombre del día en español para el selected_day
        day_name = selected_day.strftime("%A")  # en inglés
        # Mapear a español
        days_map = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }
        day_name_es = days_map.get(day_name, day_name)

        # Obtener horas ya reservadas para el día seleccionado
        from ConectaGo.models import Appointment
        appointments = Appointment.objects.filter(professional=professional_profile, date=selected_day, status='scheduled')
        booked_times = set()
        for appt in appointments:
            if appt.time:
                booked_times.add(appt.time.strftime("%H:%M"))

        # Filtrar horas disponibles para cada bloque excluyendo las ya reservadas
        morning_available = [h for h in morning_hours if is_hour_available(h, schedule, day_name_es) and h not in booked_times]
        afternoon_available = [h for h in afternoon_hours if is_hour_available(h, schedule, day_name_es) and h not in booked_times]
        night_available = [h for h in night_hours if is_hour_available(h, schedule, day_name_es) and h not in booked_times]

        # Filtrar horas según fecha y hora actual
        now = datetime.datetime.now()
        if selected_day < now.date():
            # Día pasado: no mostrar horas disponibles
            morning_available = []
            afternoon_available = []
            night_available = []
        elif selected_day == now.date():
            # Día actual: filtrar horas anteriores a la hora actual
            def filter_past_hours(hours):
                filtered = []
                for h in hours:
                    hour_int = int(h.split(':')[0])
                    # Cambiar para que solo muestre horas que estén al menos 3 horas adelante de la hora actual
                    if hour_int >= now.hour:
                        filtered.append(h)
                return filtered

            morning_available = filter_past_hours(morning_available)
            afternoon_available = filter_past_hours(afternoon_available)
            night_available = filter_past_hours(night_available)

        logging.info(f"Visualizando horario para {username} en día {selected_day}, schedule: {schedule}")

        day_schedule = schedule.get(day_name_es, {})

        # Obtener servicios (prices) del profesional
        services_qs = professional_profile.prices.all()

        from django.utils.formats import number_format
        services = []
        for service in services_qs:
            formatted_price = number_format(service.price, decimal_pos=0, use_l10n=True, force_grouping=True)
            # Reemplazar punto decimal por coma para formato chileno
            formatted_price = formatted_price.replace('.', ',')
            # Reemplazar separador de miles (coma o punto) por espacio
            formatted_price = formatted_price.replace(',', ' ').replace('.', ' ')
            services.append({
                'id': service.id,
                'description': service.description,
                'formatted_price': formatted_price,
            })

        contexto = {
            'professional_profile': professional_profile,
            'schedule': schedule,
            'day_schedule': day_schedule,
            'selected_day': selected_day,
            'morning_hours': morning_hours,
            'afternoon_hours': afternoon_hours,
            'night_hours': night_hours,
            'morning_available': morning_available,
            'afternoon_available': afternoon_available,
            'night_available': night_available,
            'services': services,
        }
        return render(request, 'vistas/professional_schedule.html', contexto)
    except Exception as e:
        logging.error(f"Error en professional_schedule_view para username {username}: {e}", exc_info=True)
        raise

from ConectaGo.models import Review, ProfessionalProfile, ClientProfile

def nosotros(request):
    try:
        admin_user = User.objects.filter(email='admin@admin.com').first()
        admin_profile = AdminProfile.objects.filter(user=admin_user).first() if admin_user else None
    except Exception:
        admin_user = None
        admin_profile = None

    # Calcular profesionales activos
    profesionales_activos = ProfessionalProfile.objects.count()

    # Obtener clientes que han dado alguna valoración
    clientes_que_valoraron = Review.objects.values_list('client', flat=True).distinct()

    # Clientes satisfechos: clientes que han dado rating >= 4
    clientes_satisfechos_qs = Review.objects.filter(rating__gte=4).values_list('client', flat=True).distinct()
    clientes_satisfechos = clientes_satisfechos_qs.count()

    # Total clientes que han dado valoración (para índice de satisfacción)
    total_clientes_valoraron = clientes_que_valoraron.count()

    # Calcular índice de satisfacción (porcentaje)
    indice_satisfaccion = 0
    if total_clientes_valoraron > 0:
        indice_satisfaccion = (clientes_satisfechos / total_clientes_valoraron) * 100

    # Formatear números con separadores de miles para mostrar en template sin usar filtros
    clientes_satisfechos_str = f"{clientes_satisfechos:,}".replace(",", ".")
    profesionales_activos_str = f"{profesionales_activos:,}".replace(",", ".")

    contexto = {
        'admin_user': admin_user,
        'admin_profile': admin_profile,
        'clientes_satisfechos_str': clientes_satisfechos_str,
        'profesionales_activos_str': profesionales_activos_str,
        'indice_satisfaccion': round(indice_satisfaccion, 2),
    }
    return render(request, 'vistas/nosotros.html', contexto)

@login_required
def mis_citas_profesional_view(request):
    from ConectaGo.models import Appointment
    import datetime

    user = request.user
    try:
        professional_profile = ProfessionalProfile.objects.get(user=user)
    except ProfessionalProfile.DoesNotExist:
        raise Http404("Perfil profesional no encontrado")

    # Delete old appointments with status 'scheduled' and date in the past
    now = datetime.datetime.now().date()
    old_appointments = Appointment.objects.filter(professional=professional_profile, status='scheduled', date__lt=now)
    old_appointments.delete()

    # Mark upcoming scheduled appointments as seen (notification acknowledged)
    upcoming_appointments = Appointment.objects.filter(
        professional=professional_profile,
        status='scheduled',
        date__gte=now,
        notification_seen=False
    )
    upcoming_appointments.update(notification_seen=True)

    # Get appointments for this professional
    appointments = Appointment.objects.filter(professional=professional_profile).order_by('-date')

    contexto = {
        'appointments': appointments,
    }
    return render(request, 'vistas/mis_citas_profesional.html', contexto)

@login_required
def cliente_citas(request):
    from ConectaGo.models import Appointment
    import datetime

    user = request.user
    try:
        client_profile = user.clientprofile
    except Exception:
        messages.error(request, "No tienes un perfil de cliente. Por favor, crea tu perfil para ver tus citas.")
        return redirect('ConectaGo:client_profile_edit')

    # Delete old appointments with status 'scheduled' and date in the past
    now = datetime.datetime.now().date()
    old_appointments = Appointment.objects.filter(client=client_profile, status='scheduled', date__lt=now)
    old_appointments.delete()

    # Mark upcoming scheduled appointments as seen (reminder acknowledged)
    upcoming_appointments = Appointment.objects.filter(
        client=client_profile,
        status='scheduled',
        date__gte=now,
        notification_seen=False
    )
    upcoming_appointments.update(notification_seen=True)

    # Get appointments for this client
    appointments = Appointment.objects.filter(client=client_profile).order_by('-date')

    # Annotate each appointment with display status and color
    for appt in appointments:
        status_info = appt.get_status_with_time()
        appt.display_status = status_info['text']
        appt.status_color = status_info['color']

    contexto = {
        'appointments': appointments,
    }
    return render(request, 'vistas/cliente_citas.html', contexto)

@login_required
def delete_appointment_view(request, appointment_id):
    from ConectaGo.models import Appointment
    import datetime

    if request.method == 'POST':
        user = request.user
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            messages.error(request, 'Cita no encontrada.')
            return redirect('ConectaGo:mis_citas_profesional')

        # Only allow deletion if appointment date is in the past
        if appointment.professional.user != user:
            messages.error(request, 'No tienes permiso para eliminar esta cita.')
            return redirect('ConectaGo:mis_citas_profesional')

        if appointment.date >= datetime.datetime.now().date():
            messages.error(request, 'Solo se pueden eliminar citas pasadas.')
            return redirect('ConectaGo:mis_citas_profesional')

        appointment.delete()
        messages.success(request, 'Cita eliminada correctamente.')
        return redirect('ConectaGo:mis_citas_profesional')

@login_required
def cancel_appointment_view(request, appointment_id):
    from ConectaGo.models import Appointment, ChatRoom, ChatMessage
    import datetime
    import logging

    if request.method == 'POST':
        user = request.user
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            messages.error(request, 'Cita no encontrada.')
            logging.warning(f"Cancel appointment: Appointment {appointment_id} not found for user {user}")
            return redirect('ConectaGo:home')

        # Debug logging for permission check
        logging.info(f"Cancel appointment: User {user} attempting to cancel appointment {appointment_id} with client {appointment.client.user if appointment.client else 'None'} and professional {appointment.professional.user if appointment.professional else 'None'}")

        # Only allow cancellation if appointment belongs to the client or professional
        if not ((appointment.client and appointment.client.user == user) or (appointment.professional and appointment.professional.user == user)):
            messages.error(request, 'No tienes permiso para cancelar esta cita.')
            logging.warning(f"Cancel appointment: User {user} has no permission to cancel appointment {appointment_id}")
            return redirect('ConectaGo:home')

        # Allow cancellation only if appointment date is in the future or today
        if appointment.date < datetime.datetime.now().date():
            messages.error(request, 'No se puede cancelar una cita pasada.')
            logging.warning(f"Cancel appointment: Appointment {appointment_id} is in the past, cannot cancel")
            return redirect('ConectaGo:home')

        cancel_reason = request.POST.get('cancel_reason', '').strip()
        appointment.status = 'cancelled'
        appointment.cancel_reason = cancel_reason if cancel_reason else None
        appointment.save()

        # Send chat message to the other user
        other_user = None
        if appointment.client and appointment.client.user == user:
            other_user = appointment.professional.user
        elif appointment.professional and appointment.professional.user == user:
            other_user = appointment.client.user

        if other_user:
            # Find or create chatroom between users
            chatroom = ChatRoom.objects.filter(participants=user).filter(participants=other_user).first()
            if not chatroom:
                chatroom = ChatRoom.objects.create()
                chatroom.participants.add(user, other_user)
                chatroom.save()

            message_content = f"La cita ha sido cancelada. Motivo: {cancel_reason}" if cancel_reason else "La cita ha sido cancelada."
            ChatMessage.objects.create(
                chatroom=chatroom,
                sender=user,
                content=message_content
            )

        messages.success(request, 'Cita cancelada correctamente.')
        logging.info(f"Cancel appointment: Appointment {appointment_id} cancelled by user {user}")
        return redirect('ConectaGo:home')

@login_required
def modify_appointment_view(request, appointment_id):
    # Placeholder for modify appointment functionality
    messages.info(request, 'Funcionalidad de modificar cita aún no implementada.')
    return redirect('ConectaGo:cliente_citas')

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(["GET", "POST"])
def validar_cita_view(request):
    from ConectaGo.models import Appointment, ClientProfile, Price
    import datetime as dt

    def schedule_appointment_db(user, professional_profile, service_id, date, time):
        try:
            service = professional_profile.prices.get(id=service_id)
        except Price.DoesNotExist:
            return False, "Servicio no encontrado."

        try:
            time_obj = dt.datetime.strptime(time, "%H:%M").time()
        except Exception:
            time_obj = None

        client_profile = None
        if user.is_authenticated:
            try:
                client_profile = ClientProfile.objects.get(user=user)
            except ClientProfile.DoesNotExist:
                client_profile = None

        Appointment.objects.create(
            professional=professional_profile,
            client=client_profile,
            service=service,
            date=dt.datetime.strptime(date, "%Y-%m-%d").date(),
            time=time_obj,
            status='scheduled'
        )
        return True, "Cita agendada correctamente."

    if request.method == "GET":
        # Get parameters from query string
        service_id = request.GET.get('service_id')
        date = request.GET.get('date')
        time = request.GET.get('time')
        username = request.GET.get('username')

        if not all([service_id, date, time, username]):
            messages.error(request, "Faltan datos para validar la cita.")
            if username:
                return redirect('ConectaGo:professional_schedule', username=username)
            else:
                return redirect('ConectaGo:home')

        try:
            user = User.objects.get(username=username)
            professional_profile = ProfessionalProfile.objects.get(user=user)
            service = professional_profile.prices.get(id=service_id)
        except (User.DoesNotExist, ProfessionalProfile.DoesNotExist, Exception):
            messages.error(request, "Datos inválidos para validar la cita.")
            if username:
                return redirect('ConectaGo:professional_schedule', username=username)
            else:
                return redirect('ConectaGo:home')

        # Get client profile if logged in
        client_profile = None
        if request.user.is_authenticated:
            try:
                client_profile = request.user.clientprofile
            except Exception:
                client_profile = None

        show_success_popup = request.GET.get('success') == '1'
        client_message = request.GET.get('client_message', '')
        context = {
            'service': service,
            'date': date,
            'time': time,
            'professional_profile': professional_profile,
            'username': username,
            'client_profile': client_profile,
            'user': request.user,
            'show_success_popup': show_success_popup,
            'client_message': client_message,
        }
        return render(request, 'vistas/validar_cita.html', context)

    elif request.method == "POST":
        # Confirm the appointment
        service_id = request.POST.get('service_id')
        date = request.POST.get('date')
        time = request.POST.get('time')
        username = request.POST.get('username')

        direccion = request.POST.get('direccion')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        mensaje = request.POST.get('mensaje', '').strip()

        if not all([service_id, date, time, username, direccion, nombre, apellido, email, telefono]):
            messages.error(request, "Faltan datos para confirmar la cita.")
            if username:
                return redirect('ConectaGo:professional_schedule', username=username)
            else:
                return redirect('ConectaGo:home')

        try:
            user = User.objects.get(username=username)
            professional_profile = ProfessionalProfile.objects.get(user=user)
        except (User.DoesNotExist, ProfessionalProfile.DoesNotExist, Exception):
            messages.error(request, "Datos inválidos para confirmar la cita.")
            if username:
                return redirect('ConectaGo:professional_schedule', username=username)
            else:
                return redirect('ConectaGo:home')

        # Update or create client profile
        client_user = request.user
        if client_user.is_authenticated:
            try:
                client_profile = client_user.clientprofile
                client_profile.nombre = nombre
                client_profile.apellido = apellido
                client_profile.ubicacion = direccion
                client_profile.save()
            except ClientProfile.DoesNotExist:
                ClientProfile.objects.create(
                    user=client_user,
                    nombre=nombre,
                    apellido=apellido,
                    ubicacion=direccion
                )
            # Update user email and name if different
            if client_user.email != email:
                client_user.email = email
                client_user.username = email
                client_user.first_name = nombre
                client_user.last_name = apellido
                client_user.save()

        # Schedule appointment with client message
        from ConectaGo.models import Appointment
        import datetime as dt

        try:
            service = professional_profile.prices.get(id=service_id)
        except Exception:
            messages.error(request, "Servicio no encontrado.")
            if username:
                return redirect('ConectaGo:professional_schedule', username=username)
            else:
                return redirect('ConectaGo:home')

        try:
            time_obj = dt.datetime.strptime(time, "%H:%M").time()
        except Exception:
            time_obj = None

        appointment = Appointment.objects.create(
            professional=professional_profile,
            client=client_user.clientprofile if client_user.is_authenticated else None,
            service=service,
            date=dt.datetime.strptime(date, "%Y-%m-%d").date(),
            time=time_obj,
            status='scheduled',
            client_message=mensaje,
            notification_seen=False
        )

        # Check if this is a reschedule by looking for a recently cancelled appointment with matching client and professional
        from ConectaGo.models import Appointment, ChatRoom, ChatMessage
        import datetime as dt2

        reschedule_reason = None
        old_appointment = Appointment.objects.filter(
            client=client_user.clientprofile if client_user.is_authenticated else None,
            professional=professional_profile,
            status='cancelled',
            cancel_reason__startswith='Reagendado:'
        ).order_by('-date', '-id').first()

        if old_appointment:
            reschedule_reason = old_appointment.cancel_reason[len('Reagendado:'):].strip()
            other_user = None
            if old_appointment.client and old_appointment.client.user == client_user:
                other_user = old_appointment.professional.user
            elif old_appointment.professional and old_appointment.professional.user == client_user:
                other_user = old_appointment.client.user

            if other_user:
                chatroom = ChatRoom.objects.filter(participants=client_user).filter(participants=other_user).first()
                if not chatroom:
                    chatroom = ChatRoom.objects.create()
                    chatroom.participants.add(client_user, other_user)
                    chatroom.save()

                # Format date and time for message
                date_str = appointment.date.strftime('%d de %B de %Y')
                time_str = appointment.time.strftime('%H:%M') if appointment.time else ''

                message_content = f"La cita ha sido reagendada para el {date_str} a las {time_str}. Motivo: {reschedule_reason}"
                ChatMessage.objects.create(
                    chatroom=chatroom,
                    sender=client_user,
                    content=message_content
                )

        messages.success(request, "Cita agendada correctamente.")
        # Redirect back to validar_cita with success flag
        return redirect(f"{reverse('ConectaGo:validar_cita')}?service_id={service_id}&date={date}&time={time}&username={username}&success=1")

# Original schedule_appointment_view remains unchanged
def schedule_appointment_view(request, username):
    try:
        data = json.loads(request.body)
        service_id = data.get('service_id')
        date = data.get('date')
        time = data.get('time')

        if not all([service_id, date, time]):
            return JsonResponse({'error': 'Faltan datos requeridos.'}, status=400)

        try:
            user = User.objects.get(username=username)
            professional_profile = ProfessionalProfile.objects.get(user=user)
        except (User.DoesNotExist, ProfessionalProfile.DoesNotExist):
            return JsonResponse({'error': 'Perfil profesional no encontrado.'}, status=404)

        # Obtener el servicio (Price) seleccionado
        try:
            service = professional_profile.prices.get(id=service_id)
        except Exception:
            return JsonResponse({'error': 'Servicio no encontrado.'}, status=404)

        # Preparar datos para la API de Calendly
        calendly_api_key = os.getenv('CALENDLY_API_KEY')
        if not calendly_api_key:
            return JsonResponse({'error': 'API key de Calendly no configurada.'}, status=500)

        # Construir la fecha y hora en formato ISO 8601 para Calendly
        # Suponemos que la hora está en formato HH:MM y la fecha en YYYY-MM-DD
        start_time_iso = f"{date}T{time}:00Z"  # Ajustar zona horaria si es necesario

        # Aquí se debe obtener el URI del evento de Calendly para el profesional
        # Esto depende de cómo se haya configurado Calendly, por ejemplo:
        # event_uri = professional_profile.calendly_event_uri
        # Para este ejemplo, asumiremos que está almacenado en professional_profile.calendly_event_uri
        event_uri = getattr(professional_profile, 'calendly_event_uri', None)
        if not event_uri:
            return JsonResponse({'error': 'Evento de Calendly no configurado para este profesional.'}, status=500)

        # Crear la cita en Calendly
        url = "https://api.calendly.com/scheduled_events"
        headers = {
            "Authorization": f"Bearer {calendly_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "event": event_uri,
            "start_time": start_time_iso,
            "end_time": start_time_iso,  # Ajustar duración si es necesario
            "invitee": {
                "name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
                "questions_and_answers": [
                    {
                        "question": "Servicio",
                        "answer": service.description
                    }
                ]
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code in (200, 201):
            # Save appointment locally
            from ConectaGo.models import Appointment, ClientProfile
            client_profile = None
            if request.user.is_authenticated:
                try:
                    client_profile = ClientProfile.objects.get(user=request.user)
                except ClientProfile.DoesNotExist:
                    client_profile = None

            # Parse time string to time object
            import datetime as dt
            try:
                time_obj = dt.datetime.strptime(time, "%H:%M").time()
            except Exception:
                time_obj = None

            Appointment.objects.create(
                professional=professional_profile,
                client=client_profile,
                service=service,
                date=dt.datetime.strptime(date, "%Y-%m-%d").date(),
                time=time_obj,
                status='scheduled'
            )
            return JsonResponse({'message': 'Cita agendada correctamente.'})
        else:
            logging.error(f"Calendly API error response: {response.status_code} - {response.text}")
            return JsonResponse({'error': 'Error al agendar la cita en Calendly.', 'details': response.text}, status=500)

    except Exception as e:
        logging.error(f"Exception in schedule_appointment_view: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@csrf_exempt
def poblar_tablas_view(request):
    if request.method == 'POST':
        from io import StringIO
        out = StringIO()
        try:
            call_command('populate_db', stdout=out)
            return JsonResponse({'ok': True, 'output': out.getvalue()})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
