from django.urls import path, include
from . import views
from . import views_payment
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

app_name = 'ConectaGo'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('client/profile/edit/', views.client_profile_edit, name='client_profile_edit'),
    path('professional/profile/edit/', views.professional_profile_edit, name='professional_profile_edit'),
    path('client_register/', views.client_register, name='client_register'),
    path('professional_register/', views.professional_register, name='professional_register'),
    path('admin_user_list/', views.admin_user_list, name='admin_user_list'),
    path('mi_perfil_profesional/', views.mi_perfil_profesional_view, name='mi_perfil_profesional'),
    path('mis_citas_profesional/', views.mis_citas_profesional_view, name='mis_citas_profesional'),
    path('cliente_citas/', views.cliente_citas, name='cliente_citas'),
    path('professional/<str:username>/', views.public_professional_profile_view, name='public_professional_profile'),
    path('professional_schedule/<str:username>/', views.professional_schedule_view, name='professional_schedule'),
    path('schedule_appointment/<str:username>/', views.schedule_appointment_view, name='schedule_appointment'),
    path('validar_cita/', views.validar_cita_view, name='validar_cita'),
    path('admin_profile_edit/', views.admin_profile_edit, name='admin_profile_edit'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('borrar_cuenta/', views.borrar_cuenta_profesional_view, name='borrar_cuenta_profesional'),
    path('borrar_cuenta_cliente/', views.borrar_cuenta_cliente_view, name='borrar_cuenta_cliente'),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
    path('delete_user/<str:user_type>/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('delete_appointment/<int:appointment_id>/', views.delete_appointment_view, name='delete_appointment'),
    path('admin_analisis/', views.admin_analisis_view, name='admin_analisis'),
    path('admin_analisis/pdf/', views.admin_analisis_pdf_view, name='admin_analisis_pdf'),
    path('cancel_appointment/<int:appointment_id>/', views.cancel_appointment_view, name='cancel_appointment'),
    path('modify_appointment/<int:appointment_id>/', views.modify_appointment_view, name='modify_appointment'),
    path('report_review/<int:review_id>/', views.report_review, name='report_review'),
    path('reportes/', views.report_list, name='reportes'),
    path('delete_review/<int:review_id>/', views.delete_review_view, name='delete_review'),
    path('reschedule_appointment/<int:appointment_id>/', views.reschedule_appointment_view, name='reschedule_appointment'),
    path('admin_certification_management/', views.admin_certification_management, name='admin_certification_management'),
    path('chat/', views.chat_view, name='chat'),
    path('delete_chatroom/<int:chatroom_id>/', views.delete_chatroom_view, name='delete_chatroom'),
    path('send_message/', views.send_message_view, name='send_message'),
    path('poblar_tablas/', views.poblar_tablas_view, name='poblar_tablas'),
    path('metodo_de_pago/<int:appointment_id>/', views.metodo_de_pago, name='metodo_de_pago'),
    path('pago_online/<int:appointment_id>/', views.pago_online, name='pago_online'),
    path('pago_efectivo/<int:appointment_id>/', views.pago_efectivo, name='pago_efectivo'),
    path('webpay_simulacion_pago/<int:appointment_id>/', views_payment.webpay_simulacion_pago, name='webpay_simulacion_pago'),
    path('webpay_resultado/', views_payment.webpay_resultado, name='webpay_resultado'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
