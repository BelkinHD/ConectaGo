from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Asignar permisos de superusuario a un usuario especificado'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario al que se le asignará el estado de superusuario')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        try:
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Permisos de superusuario asignados correctamente a {username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El usuario {username} no existe'))
