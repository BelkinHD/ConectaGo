from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ConectaGo.models import ClientProfile, ProfessionalProfile, AdminProfile

class Command(BaseCommand):
    help = 'Lista todos los usuarios con todos sus datos ordenados por username'

    def handle(self, *args, **kwargs):
        users = User.objects.all().order_by('username')
        if not users:
            self.stdout.write("No se encontraron usuarios.")
            return

        for user in users:
            self.stdout.write(f"Usuario: {user.username}")
            self.stdout.write(f"  Email: {user.email}")
            self.stdout.write(f"  Nombre: {user.first_name}")
            self.stdout.write(f"  Apellido: {user.last_name}")

            # Check for ClientProfile
            try:
                client_profile = ClientProfile.objects.get(user=user)
                self.stdout.write("  Perfil Cliente:")
                self.stdout.write(f"    Nombre: {client_profile.nombre}")
                self.stdout.write(f"    Apellido: {client_profile.apellido}")
                self.stdout.write(f"    Ubicación: {client_profile.ubicacion}")
                self.stdout.write(f"    Foto: {client_profile.foto.url if client_profile.foto else 'No tiene foto'}")
            except ClientProfile.DoesNotExist:
                pass

            # Check for ProfessionalProfile
            try:
                professional_profile = ProfessionalProfile.objects.get(user=user)
                self.stdout.write("  Perfil Profesional:")
                self.stdout.write(f"    Nombre: {professional_profile.nombre}")
                self.stdout.write(f"    Apellido: {professional_profile.apellido}")
                self.stdout.write(f"    Especialidad: {professional_profile.especialidad}")
                self.stdout.write(f"    Ubicación: {professional_profile.ubicacion}")
                self.stdout.write(f"    Foto: {professional_profile.foto.url if professional_profile.foto else 'No tiene foto'}")
                self.stdout.write(f"    Experiencia: {professional_profile.experiencia or 'No especificada'}")
                self.stdout.write(f"    Descripción: {professional_profile.descripcion or 'No especificada'}")
                # Added fields
                self.stdout.write(f"    Nombre Certificado: {professional_profile.nombre_certificado or 'No especificado'}")
                self.stdout.write(f"    Entidad Emisora: {professional_profile.entidad_emisora or 'No especificada'}")
                self.stdout.write(f"    Fecha Emisión: {professional_profile.fecha_emision or 'No especificada'}")
                self.stdout.write(f"    Archivo PDF: {professional_profile.archivo_pdf.url if professional_profile.archivo_pdf else 'No especificado'}")
            except ProfessionalProfile.DoesNotExist:
                pass

            # Check for AdminProfile
            try:
                admin_profile = AdminProfile.objects.get(user=user)
                self.stdout.write("  Perfil Administrador:")
                self.stdout.write(f"    Foto: {admin_profile.foto.url if admin_profile.foto else 'No tiene foto'}")
            except AdminProfile.DoesNotExist:
                pass

            self.stdout.write("-" * 50)
