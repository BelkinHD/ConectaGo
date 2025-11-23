from django.urls import path
from . import views_payment

app_name = 'payment'

urlpatterns = [
    path('initiate/', views_payment.initiate_payment, name='initiate_payment'),
]
