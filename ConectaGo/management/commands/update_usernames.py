from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ConectaGo.models import ClientProfile, ProfessionalProfile

class Command(BaseCommand):
    help = 'Actualizar usernames de usuarios para que coincidan con nombre completo'

    def handle(self, *args, **kwargs):
        # Actualizar usernames de clientes
        clientes = ClientProfile.objects.all()
        for cliente in clientes:
            user = cliente.user
            nuevo_username = f"{cliente.nombre} {cliente.apellido}"
            if user.username != nuevo_username:
                self.stdout.write(f"Actualizando username cliente ID {user.id} de '{user.username}' a '{nuevo_username}'")
                user.username = nuevo_username
                user.save()

        # Actualizar usernames de profesionales
        profesionales = ProfessionalProfile.objects.all()
        for profesional in profesionales:
            user = profesional.user
            nuevo_username = f"{profesional.nombre} {profesional.apellido}"
            if user.username != nuevo_username:
                self.stdout.write(f"Actualizando username profesional ID {user.id} de '{user.username}' a '{nuevo_username}'")
                user.username = nuevo_username
                user.save()

        self.stdout.write(self.style.SUCCESS('Actualización de usernames completada.'))
