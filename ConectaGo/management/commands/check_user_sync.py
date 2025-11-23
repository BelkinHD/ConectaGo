from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Verifica la sincronización de usernames y emails entre la base de datos y los perfiles'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        inconsistencies = 0
        for user in users:
            username = user.username
            email = user.email
            if username != email:
                self.stdout.write(self.style.WARNING(
                    f'Inconsistencia detectada: username="{username}" no coincide con email="{email}" para usuario ID {user.id}'
                ))
                inconsistencies += 1
        if inconsistencies == 0:
            self.stdout.write(self.style.SUCCESS('Todos los usernames coinciden con los emails.'))
        else:
            self.stdout.write(self.style.ERROR(f'Se encontraron {inconsistencies} inconsistencias.'))
