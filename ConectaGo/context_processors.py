def google_maps_api_key(request):
    return {
        'google_maps_api_key': 'AIzaSyCo9E96ubTQ8C-4KtQ1kZUXBqkJwWH5seQ'
    }

from django.utils import timezone
from ConectaGo.models import Appointment, ProfessionalProfile

def professional_appointments_notifications(request):
    user = request.user
    notifications = {
        'appointment_count': 0,
        'appointments': [],
        'certification_notifications': [],
        'certification_count': 0,
    }
    if user.is_authenticated:
        try:
            professional_profile = user.professionalprofile
            today = timezone.now().date()
            upcoming_appointments = Appointment.objects.filter(
                professional=professional_profile,
                status='scheduled',
                notification_seen=False,
                date__gte=today
            ).order_by('date', 'time')[:10]

            count = upcoming_appointments.count()
            notifications['appointment_count'] = count
            notifications['appointments'] = upcoming_appointments

            # Fetch unread certification rejection notifications
            from ConectaGo.models import Notification
            cert_notifications = Notification.objects.filter(
                user=user,
                read=False,
                message__icontains='certificación ha sido rechazada'
            ).order_by('-created_at')[:10]

            notifications['certification_notifications'] = cert_notifications
            notifications['certification_count'] = cert_notifications.count()

            # Add certification count to total appointment count for badge
            notifications['appointment_count'] += notifications['certification_count']

        except ProfessionalProfile.DoesNotExist:
            pass
    return {
        'appointment_notifications': notifications
    }
