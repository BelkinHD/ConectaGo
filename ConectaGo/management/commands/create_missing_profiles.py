from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ConectaGo.models import ClientProfile, ProfessionalProfile

class Command(BaseCommand):
    help = 'Crear objetos ClientProfile y ProfessionalProfile faltantes para usuarios existentes'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_client_profiles = 0
        created_professional_profiles = 0

        for user in users:
            if not hasattr(user, 'clientprofile') and not hasattr(user, 'professionalprofile'):
                # Crear ClientProfile para todos los usuarios sin perfiles
                ClientProfile.objects.create(
                    user=user,
                    nombre=user.username,
                    apellido='',
                    ubicacion='Desconocida'
                )
                created_client_profiles += 1
                self.stdout.write(f'ClientProfile creado para el usuario {user.username}')

        self.stdout.write(self.style.SUCCESS(
            f'Se crearon {created_client_profiles} ClientProfiles y {created_professional_profiles} ProfessionalProfiles.'
        ))
