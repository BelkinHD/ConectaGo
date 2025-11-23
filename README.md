# Conecta.go

## Descripción
Conecta.go es una plataforma diseñada para conectar a usuarios con profesionales confiables para servicios domiciliarios. El proyecto utiliza tecnologías modernas como Django y Docker para garantizar un entorno eficiente y escalable. Además, incluye funcionalidades avanzadas como gestión de certificaciones, opiniones de clientes y análisis de datos.

## Características Principales
- **Gestión de perfiles profesionales**: Los profesionales pueden registrar sus perfiles, incluyendo certificaciones, horarios de atención y servicios ofrecidos.
- **Sistema de citas**: Los usuarios pueden agendar citas con profesionales según disponibilidad y recibir confirmaciones.
- **Opiniones y calificaciones**: Los clientes pueden dejar opiniones y calificaciones sobre los servicios recibidos, con opciones para reportar comentarios inapropiados.
- **Panel de administración**: Los administradores pueden gestionar usuarios, certificaciones, reportes y realizar análisis de datos.
- **Integración con Google Maps**: Permite a los usuarios localizar profesionales cercanos y visualizar ubicaciones.
- **Generación de reportes en PDF**: Los administradores pueden generar reportes detallados sobre profesionales y citas.

## Instalación
### Requisitos
- **Docker**: Herramienta para crear y gestionar contenedores que permiten ejecutar aplicaciones en entornos aislados.
- **Docker Compose**: Utilidad para definir y ejecutar aplicaciones multi-contenedor mediante un archivo YAML.
- **Git**: Sistema de control de versiones para clonar y gestionar el repositorio.

### Manual de Instalación
1. **Clonar el repositorio**:
   ```bash
   git clone <URL-del-repositorio>
   ```
   Esto descarga el código fuente del proyecto desde el repositorio remoto.
2. **Navegar al directorio del proyecto**:
   ```bash
   cd Conecta.go
   ```
   Cambia al directorio donde se encuentra el proyecto.
3. **Construir los contenedores Docker**:
   ```bash
   docker-compose build
   ```
   Este comando crea las imágenes de Docker necesarias para ejecutar el proyecto.
4. **Iniciar los contenedores**:
   Puedes usar el script `start_project.bat` para iniciar el proyecto:
   ```bash
   ./start_project.bat
   ```
   Alternativamente, puedes iniciar los contenedores manualmente:
   ```bash
   docker-compose up
   ```
   Esto inicia los servicios definidos en el archivo `docker-compose.yml`.
5. **Acceder a la aplicación**:
   Abre tu navegador y ve a `http://127.0.0.1:8000`.
6. **Detener los contenedores**:
   Usa el script `stop_project.bat` para detener el proyecto:
   ```bash
   ./stop_project.bat
   ```
   Alternativamente, puedes detener los contenedores manualmente:
   ```bash
   docker-compose down
   ```
   Esto detiene y elimina los contenedores creados.
7. **Verificar los logs**:
   Para depurar problemas, puedes verificar los logs de los contenedores:
   ```bash
   docker-compose logs
   ```
   Los logs muestran información sobre el estado de los servicios.
8. **Reiniciar servicios específicos**:
   Si necesitas reiniciar un servicio específico:
   ```bash
   docker-compose restart <nombre-del-servicio>
   ```

## Uso
1. Accede a la aplicación en tu navegador en `http://127.0.0.1:8000`.
2. Para detener los contenedores, utiliza:
   ```bash
   docker-compose down
   ```

## Estructura del Proyecto
- **App/**: Contiene la configuración principal del proyecto.
- **ConectaGo/**: Incluye las aplicaciones, vistas, modelos y plantillas.
  - **templates/**: Plantillas HTML para las vistas, organizadas por funcionalidad.
  - **static/**: Archivos estáticos como CSS y JavaScript.
  - **migrations/**: Migraciones de la base de datos.
  - **management/**: Comandos personalizados de Django.
  - **views.py**: Contiene la lógica de las vistas, incluyendo manejo de perfiles, citas y reportes.
  - **models.py**: Define los modelos de datos como usuarios, perfiles profesionales y citas.
  - **forms.py**: Formularios para la interacción con los usuarios.
  - **urls.py**: Configuración de rutas para las vistas.
- **media/**: Almacena archivos multimedia como fotos de perfil y documentos.
- **certificados/**: Archivos PDF de certificaciones.
- **Dockerfile**: Define la configuración del contenedor Docker.
- **docker-compose.yml**: Configuración para orquestar los servicios Docker.
- **start_project.bat**: Script para iniciar el proyecto.
- **stop_project.bat**: Script para detener el proyecto.

## Funcionalidades Detalladas
### Para Usuarios
- Registro y autenticación.
- Búsqueda de profesionales por ubicación y especialidad.
- Agendamiento de citas.
- Opiniones y calificaciones.

### Para Profesionales
- Registro de perfil con certificaciones y servicios ofrecidos.
- Gestión de horarios de atención.
- Visualización de citas agendadas.

### Para Administradores
- Gestión de usuarios y profesionales.
- Validación de certificaciones.
- Generación de reportes en PDF.
- Análisis de datos sobre citas y opiniones.

## Lógica Interna y Flujos de Usuario

### Flujos de Usuario
- **Usuarios**:
  - Registro y autenticación mediante formularios.
  - Búsqueda de profesionales por ubicación y especialidad.
  - Agendamiento de citas con selección de servicios y horarios disponibles.
  - Opiniones y calificaciones sobre los servicios recibidos.
- **Profesionales**:
  - Registro de perfil con datos como nombre, especialidad, ubicación y certificaciones.
  - Gestión de horarios de atención mediante formularios interactivos.
  - Visualización de citas agendadas y detalles de los clientes.
- **Administradores**:
  - Validación de certificaciones de profesionales.
  - Generación de reportes en PDF sobre citas y opiniones.
  - Análisis de datos para identificar tendencias y métricas clave.

### APIs y Funciones Internas

#### APIs Principales
- **Autenticación**:
  - `login_view`: Permite a los usuarios iniciar sesión.
  - `logout_view`: Cierra la sesión del usuario.
- **Gestión de Perfiles**:
  - `client_register`: Registro de clientes.
  - `professional_register`: Registro de profesionales.
  - `profile_view`: Visualización de perfiles.
  - `professional_profile_edit`: Edición de perfiles profesionales.
  - `client_profile_edit`: Edición de perfiles de clientes.
- **Sistema de Citas**:
  - `reschedule_appointment_view`: Reprogramación de citas.
  - `delete_appointment_view`: Eliminación de citas.
  - `validar_cita_view`: Validación y creación de citas.
- **Gestión de Opiniones**:
  - `delete_review_view`: Eliminación de opiniones.
  - `report_review`: Reporte de opiniones inapropiadas.
- **Administración**:
  - `admin_user_list`: Gestión de usuarios.
  - `admin_certification_management`: Validación de certificaciones.
  - `admin_analisis_view`: Análisis de datos y generación de reportes.

#### Funciones Internas
- **Geocodificación**:
  - `geocode_address`: Utiliza la API de Google Maps para obtener coordenadas de una dirección.
- **Mensajería**:
  - `send_message_view`: Envío de mensajes entre usuarios.
- **Chat**:
  - `chat_view`: Gestión de salas de chat.
  - `delete_chatroom_view`: Eliminación de salas de chat.

## Lógica de Negocio
- **Gestión de Certificaciones**:
  - Los administradores validan las certificaciones subidas por los profesionales.
  - Los profesionales pueden actualizar sus certificaciones desde su perfil.
- **Sistema de Citas**:
  - Los usuarios seleccionan servicios y horarios disponibles.
  - Las citas se almacenan en la base de datos con estado "agendada".
  - Los profesionales pueden gestionar sus citas y recibir notificaciones.
- **Opiniones y Calificaciones**:
  - Los clientes dejan opiniones con calificaciones de 1 a 5 estrellas.
  - Las opiniones se filtran y ordenan por fecha y calificación.
- **Análisis de Datos**:
  - Los administradores generan reportes en PDF con métricas clave como cantidad de citas y ubicaciones.

## Estructura de Datos
- **Usuarios**:
  - Datos básicos como nombre, correo electrónico y contraseña.
  - Roles: cliente, profesional y administrador.
- **Perfiles Profesionales**:
  - Especialidad, ubicación, experiencia y certificaciones.
  - Horarios de atención y servicios ofrecidos.
- **Citas**:
  - Fecha, hora, cliente, profesional y estado.
  - Mensajes opcionales del cliente.
- **Opiniones**:
  - Calificación, comentario y fecha.
  - Respuestas de los profesionales.
- **Mensajes**:
  - Contenido, remitente y destinatario.
  - Estado de lectura.

## Dependencias Clave
- **Django**: Framework principal para el desarrollo del backend.
- **Docker**: Para la creación de contenedores y gestión del entorno.
- **Docker Compose**: Orquestación de servicios en contenedores.
- **Google Maps API**: Integración para mostrar ubicaciones de profesionales.
- **ReportLab**: Generación de reportes en PDF.

## Scripts Relevantes
- **start_project.bat**: Inicia los contenedores Docker.
- **stop_project.bat**: Detiene los contenedores Docker.
- **manage.py**: Herramienta de línea de comandos para tareas de Django.

## Funcionalidades Avanzadas
- **Integración con Google Maps**:
  - Los usuarios pueden buscar profesionales cercanos.
  - Los profesionales pueden actualizar su ubicación mediante formularios interactivos.
- **Gestión de Certificaciones**:
  - Los administradores validan las certificaciones subidas por los profesionales.
  - Los profesionales pueden actualizar sus certificaciones desde su perfil.
- **Análisis de Datos**:
  - Los administradores pueden visualizar métricas clave como índice de satisfacción y cantidad de citas.
  - Los datos se presentan en tablas y gráficos interactivos.

## Integración con Google Maps y Calendly

### Google Maps API
- **Propósito**:
  - Permitir a los usuarios localizar profesionales cercanos.
  - Facilitar la actualización de ubicaciones por parte de los profesionales.
- **Uso**:
  - La API se utiliza para geocodificar direcciones y obtener coordenadas.
  - Los mapas interactivos se integran en las vistas de perfiles profesionales.
- **Funciones Relacionadas**:
  - `geocode_address`: Convierte direcciones en coordenadas geográficas.
  - Formularios interactivos para actualizar ubicaciones.
- **Configuración**:
  - Se requiere una clave de API de Google Maps.
  - La clave se configura en las variables de entorno del proyecto.

### Calendly API
- **Propósito**:
  - Facilitar la programación de citas entre usuarios y profesionales.
  - Integrar la gestión de horarios con una plataforma externa.
- **Uso**:
  - Los usuarios seleccionan servicios y horarios disponibles.
  - Las citas se sincronizan con Calendly mediante solicitudes API.
- **Funciones Relacionadas**:
  - `scheduleAppointment`: Realiza solicitudes a la API de Calendly para crear citas.
  - Formularios interactivos para seleccionar servicios y horarios.
- **Configuración**:
  - Se requiere una clave de API de Calendly.
  - La integración se realiza mediante endpoints personalizados en el backend.

### Beneficios
- **Google Maps**:
  - Mejora la experiencia del usuario al mostrar ubicaciones precisas.
  - Facilita la búsqueda de profesionales cercanos.
- **Calendly**:
  - Simplifica la gestión de citas.
  - Automatiza la sincronización de horarios y servicios.
    
## Alcance del Proyecto
### ¿Qué hace?
- **Conecta a usuarios con profesionales confiables**:
  - Facilita la búsqueda de profesionales por ubicación y especialidad.
  - Permite agendar citas de manera sencilla y rápida.
- **Gestión de perfiles profesionales**:
  - Los profesionales pueden registrar y actualizar sus perfiles, incluyendo certificaciones y horarios.
- **Opiniones y calificaciones**:
  - Los clientes pueden dejar opiniones y calificaciones sobre los servicios recibidos.
- **Panel de administración**:
  - Los administradores pueden gestionar usuarios, validar certificaciones y generar reportes.
- **Integración con Google Maps**:
  - Localización de profesionales cercanos.
- **Generación de reportes en PDF**:
  - Reportes detallados sobre profesionales y citas.

### ¿Qué no hace?
- **No realiza pagos en línea**:
  - El proyecto no incluye funcionalidades para procesar pagos o transacciones financieras.
- **No ofrece soporte técnico en tiempo real**:
  - No cuenta con un sistema de chat o soporte en vivo para resolver problemas.
- **No gestiona inventarios o productos**:
  - Está enfocado exclusivamente en servicios domiciliarios, no en la venta de productos.
- **No incluye una aplicación móvil**:
  - El alcance actual está limitado a una plataforma web.
- **No garantiza la calidad de los servicios**:
  - La plataforma conecta usuarios y profesionales, pero no interviene en la ejecución de los servicios.
