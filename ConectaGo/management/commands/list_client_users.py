from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ConectaGo.models import ClientProfile

class Command(BaseCommand):
    help = 'Lista los usuarios clientes con sus datos personales'

    def handle(self, *args, **kwargs):
        clients = ClientProfile.objects.select_related('user').all()
        if not clients:
            self.stdout.write("No se encontraron usuarios clientes.")
            return

        for client in clients:
            user = client.user
            self.stdout.write(f"Usuario: {user.username}")
            self.stdout.write(f"  Nombre: {client.nombre}")
            self.stdout.write(f"  Apellido: {client.apellido}")
            self.stdout.write(f"  Email: {user.email}")
            self.stdout.write(f"  Ubicación: {client.ubicacion}")
            self.stdout.write(f"  Foto: {client.foto.url if client.foto else 'No tiene foto'}")
            self.stdout.write("-" * 40)
