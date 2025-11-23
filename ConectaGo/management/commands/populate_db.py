from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ConectaGo.models import ClientProfile, ProfessionalProfile, AdminProfile, Price, Review, Appointment
from django.core.files import File
from django.conf import settings
import random, os, datetime

class Command(BaseCommand):
    help = 'Pobla la base de datos con usuarios, perfiles, citas, comentarios y certificaciones.'

    def handle(self, *args, **kwargs):
        # Admin
        admin_email = 'admin@admin.com'
        admin_password = 'admin123'
        admin_foto = os.path.join(settings.BASE_DIR, 'fotos_admin', random.choice(os.listdir(os.path.join(settings.BASE_DIR, 'fotos_admin'))))
        if not User.objects.filter(username=admin_email).exists():
            admin_user = User.objects.create_superuser(username=admin_email, email=admin_email, password=admin_password)
            with open(admin_foto, 'rb') as f:
                AdminProfile.objects.create(user=admin_user, foto=File(f, name=os.path.basename(admin_foto)))
            self.stdout.write(self.style.SUCCESS('Admin creado.'))
        else:
            self.stdout.write('Admin ya existe.')

        # Lista de especialidades reales (extraídas de professional_profile_edit.html)
        especialidades = [
            "Electricidad", "Instalador eléctrico Clase D", "Instalador eléctrico Clase C, B o A",
            "Técnico en mantenimiento de tableros eléctricos", "Instalador de sistemas de puesta a tierra",
            "Instalador de portones automáticos", "Técnico en domótica", "Instalador de iluminación LED profesional",
            "Gasfitería con gas", "Instalador de artefactos a gas", "Instalador de redes de gas interior",
            "Reparador de fugas de gas domiciliarias", "Instalador de calefactores de tiro balanceado o forzado",
            "Técnico en detección de fugas o presión de red de gas", "Climatización y Refrigeración",
            "Técnico en instalación de aire acondicionado tipo split", "Técnico en instalación de calefacción central o calderas",
            "Instalador de sistemas VRF o multi split", "Técnico en cámaras de refrigeración",
            "Manipulador de gases refrigerantes", "Energías Renovables", "Instalador de paneles solares fotovoltaicos",
            "Instalador de termos solares", "Técnico en sistemas híbridos solares + red eléctrica",
            "Instalador de inversores y sistemas solares conectados a red", "Albañil estructural",
            "Instalador de techumbres o cubiertas metálicas", "Constructor de ampliaciones con permiso municipal",
            "Instalador de ventanas termo-panel certificadas", "Técnico en aislación térmica certificada",
            "Técnico en mantenimiento de ascensores", "Instalador de montacargas o salvaescalas",
            "Técnico en sistemas automatizados de acceso", "Instalador de cámaras de seguridad con red eléctrica",
            "Instalador de sistemas de alarmas conectadas", "Técnico en control de acceso biométrico o digital",
            "Aplicador de plaguicidas", "Desinfectador profesional", "Mantenimiento General del Hogar",
            "Ayudante de maestro (multiuso)", "Reparador general de viviendas", "Técnico en terminaciones menores",
            "Pintor de interiores y exteriores", "Aplicador de papel mural", "Empastador y masillador de muros",
            "Instalador de cerámicas o porcelanato", "Colocador de alfombras y pisos flotantes"
        ]
        ubicaciones = [
            "Santiago, Región Metropolitana", "Valparaíso, Región de Valparaíso", "Concepción, Región del Biobío",
            "Temuco, Región de La Araucanía", "Antofagasta, Región de Antofagasta"
        ]
        descripciones = [
            "Profesional con amplia experiencia y excelente atención.",
            "Especialista certificado en su rubro, recomendado por clientes.",
            "Técnico responsable, puntual y con gran trayectoria.",
            "Experto en soluciones rápidas y eficientes.",
            "Comprometido con la calidad y la satisfacción del cliente."
        ]

        # Profesionales
        prof_fotos = os.listdir(os.path.join(settings.BASE_DIR, 'fotos_profesionales'))
        for i in range(5):
            email = f'pro{i+1}@mail.com'
            if not User.objects.filter(username=email).exists():
                user = User.objects.create_user(username=email, email=email, password='pro1234')
                foto_path = os.path.join(settings.BASE_DIR, 'fotos_profesionales', prof_fotos[i % len(prof_fotos)])
                especialidad = especialidades[i % len(especialidades)]
                ubicacion = ubicaciones[i % len(ubicaciones)]
                descripcion = descripciones[i % len(descripciones)]
                with open(foto_path, 'rb') as f:
                    prof = ProfessionalProfile.objects.create(
                        user=user,
                        nombre=f'Profesional{i+1}',
                        apellido='Apellido',
                        especialidad=especialidad,
                        ubicacion=ubicacion,
                        foto=File(f, name=os.path.basename(foto_path)),
                        experiencia='Experiencia ejemplo',
                        descripcion=descripcion,
                        nombre_certificado='Certificado ejemplo',
                        entidad_emisora='Entidad',
                        fecha_emision=datetime.date.today(),
                        certification_status='pending',
                        rating=random.uniform(3, 5)
                    )
                # Precios
                price = Price.objects.create(professional=prof, description='Servicio ejemplo', price=10000)
                self.stdout.write(self.style.SUCCESS(f'Profesional {i+1} creado.'))
            else:
                self.stdout.write(f'Profesional {i+1} ya existe.')

        # Clientes
        cli_fotos = os.listdir(os.path.join(settings.BASE_DIR, 'fotos_clientes'))
        for i in range(5):
            email = f'cli{i+1}@mail.com'
            if not User.objects.filter(username=email).exists():
                user = User.objects.create_user(username=email, email=email, password='cli1234')
                foto_path = os.path.join(settings.BASE_DIR, 'fotos_clientes', cli_fotos[i % len(cli_fotos)])
                with open(foto_path, 'rb') as f:
                    cli = ClientProfile.objects.create(
                        user=user,
                        nombre=f'Cliente{i+1}',
                        apellido='Apellido',
                        ubicacion='Ciudad',
                        foto=File(f, name=os.path.basename(foto_path))
                    )
                self.stdout.write(self.style.SUCCESS(f'Cliente {i+1} creado.'))
            else:
                self.stdout.write(f'Cliente {i+1} ya existe.')

        # Comentarios y citas
        profesionales = ProfessionalProfile.objects.all()
        clientes = ClientProfile.objects.all()
        for prof in profesionales:
            for cli in clientes:
                # Review
                Review.objects.get_or_create(
                    professional=prof,
                    client=cli,
                    nombre=cli.nombre,
                    rating=random.randint(3, 5),
                    opinion='Muy buen servicio!',
                    likes=["puntualidad"],
                    improve=["precio"],
                )
                # Cita agendada
                price = prof.prices.first()
                if price:
                    Appointment.objects.get_or_create(
                        professional=prof,
                        client=cli,
                        service=price,
                        date=datetime.date.today() + datetime.timedelta(days=random.randint(1, 30)),
                        time=datetime.time(hour=random.randint(9, 18)),
                        status='scheduled',
                    )
        self.stdout.write(self.style.SUCCESS('Poblado completo.'))
