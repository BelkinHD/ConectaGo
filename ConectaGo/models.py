from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Modelo para el perfil del cliente
class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='fotos_clientes/', null=True, blank=True)  # Foto opcional

    @property
    def foto_url(self):
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return ''

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

# Modelo para el perfil del profesional
class ProfessionalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=100)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)  # Added phone number field
    foto = models.ImageField(upload_to='fotos_profesionales/', null=True, blank=True)  # Foto opcional
    experiencia = models.TextField(null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    nombre_certificado = models.CharField(max_length=200, null=True, blank=True)
    entidad_emisora = models.CharField(max_length=200, null=True, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)
    archivo_pdf = models.FileField(upload_to='certificados/', null=True, blank=True)
    CERTIFICATION_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
    ]
    certification_status = models.CharField(max_length=10, choices=CERTIFICATION_STATUS_CHOICES, default='pending')
    certification_rejection_message = models.TextField(null=True, blank=True)
    schedule = models.JSONField(null=True, blank=True)  # Nuevo campo para almacenar horarios en formato JSON
    calendly_event_uri = models.CharField(max_length=255, null=True, blank=True)  # URI del evento de Calendly
    rating = models.FloatField(default=0.0, help_text="Valoración promedio del profesional (0 a 5)")

    @property
    def foto_url(self):
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return ''

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.especialidad}"

# Modelo para el perfil del administrador
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='fotos_admin/', null=True, blank=True)  # Foto opcional

    @property
    def foto_url(self):
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return ''

    def __str__(self):
        return f"Admin Profile: {self.user.username}"

class Price(models.Model):
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='prices')
    description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.description} - {self.price}"

class Review(models.Model):
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='reviews')
    client = models.ForeignKey(ClientProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    nombre = models.CharField(max_length=100)  # Nombre del cliente (puede ser anónimo)
    rating = models.PositiveSmallIntegerField()
    opinion = models.TextField(max_length=500)
    likes = models.JSONField(null=True, blank=True)
    improve = models.JSONField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.professional.nombre} ({self.rating} estrellas)"

class Reply(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='replies')
    texto = models.TextField(max_length=500)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Respuesta de {self.professional.nombre} a {self.review.nombre} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    professional = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='appointments')
    client = models.ForeignKey(ClientProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    service = models.ForeignKey(Price, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    cancel_reason = models.TextField(null=True, blank=True)  # New field for cancellation reason
    client_message = models.TextField(null=True, blank=True)  # New field for client message
    notification_seen = models.BooleanField(default=False)  # Added field for notification seen status
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cita con {self.professional} el {self.date} a las {self.time} - {self.status}"

    @property
    def status_display(self):
        status_map = {
            'scheduled': 'Agendada',
            'cancelled': 'Cancelada',
            'completed': 'Completada',
        }
        return status_map.get(self.status, self.status)

    def get_status_with_time(self):
        import datetime
        from django.utils.timezone import localtime, now, make_aware

        # Combine date and time into a naive datetime object
        naive_appointment_datetime = datetime.datetime.combine(self.date, self.time)

        # Make appointment_datetime timezone-aware using current timezone
        appointment_datetime = make_aware(naive_appointment_datetime)

        # Get current local time
        current_time = localtime(now())

        # Calculate time difference in seconds
        diff = (appointment_datetime - current_time).total_seconds()

        # If appointment is cancelled or completed, just return status display with default color
        if self.status in ['cancelled', 'completed']:
            return {'text': self.status_display, 'color': 'black'}

        # If appointment is in progress (within 1 hour window)
        if -3600 <= diff <= 0:
            return {'text': 'En curso', 'color': 'green'}

        # If appointment is upcoming
        if diff > 0:
            hours = int(diff // 3600)
            minutes = int((diff % 3600) // 60)
            time_str = 'dentro de '
            if hours > 0:
                time_str += f"{hours}"
                if hours > 1:
                    time_str += "horas "
                if minutes > 0:
                    time_str += " y "
            if minutes > 0:
                time_str += f"{minutes} minutos"
            return {'text': time_str, 'color': 'black'}

        # If appointment is past but not completed or cancelled
        return {'text': self.status_display, 'color': 'black'}

class Report(models.Model):
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='reports')
    justification = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Report by {self.reporter} on review {self.review.id} - {self.status}"

class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name='chatrooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatRoom {self.id} - Participants: {', '.join([user.username for user in self.participants.all()])}"

class ChatMessage(models.Model):
    chatroom = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='chatmessages_sent', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"ChatMessage {self.id} from {self.sender.username} at {self.timestamp}"

class Notification(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {'Read' if self.read else 'Unread'}"

class ProfessionalPhoto(models.Model):
    professional = models.ForeignKey('ProfessionalProfile', on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='professional_photos/')
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo of {self.professional.nombre} {self.professional.apellido} - {self.description[:20]}"

