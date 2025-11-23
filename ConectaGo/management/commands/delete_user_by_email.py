from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Elimina un usuario dado su correo electrónico'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Correo electrónico del usuario a eliminar')

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        users = User.objects.filter(email=email)
        if not users.exists():
            self.stdout.write(self.style.ERROR(f'No se encontró usuario con email {email}.'))
            return
        count = users.count()
        users.delete()
        self.stdout.write(self.style.SUCCESS(f'Se eliminaron {count} usuario(s) con email {email}.'))
