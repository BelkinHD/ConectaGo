from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.template import loader
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType
from ConectaGo.models import Appointment
from django.shortcuts import get_object_or_404
from django.conf import settings

def initiate_payment(request):
    # Placeholder view for initiate_payment
    return HttpResponse("Payment initiation page - to be implemented.")

def webpay_simulacion_pago(request, appointment_id):
    # Realistic Webpay payment simulation for an appointment
    appointment = get_object_or_404(Appointment, id=appointment_id)
    # Get the price of the appointment's service
    price = appointment.service.price if appointment.service else 0

    # Setup Webpay transaction (correct para SDK 4.x, método de instancia)
    transaction = Transaction()
    transaction.configure_for_integration(
        commerce_code=IntegrationCommerceCodes.WEBPAY_PLUS,
        api_key=IntegrationApiKeys.WEBPAY
    )

    # Create a transaction
    buy_order = f"order_{appointment_id}"
    session_id = f"session_{appointment_id}"
    return_url = request.build_absolute_uri(reverse('ConectaGo:webpay_resultado'))

    response = transaction.create(
        buy_order=buy_order,
        session_id=session_id,
        amount=float(price),
        return_url=return_url
    )

    # Renderiza un formulario auto-submit para POST a Webpay
    context = {
        'webpay_url': response['url'],
        'token': response['token'],
    }
    template = loader.get_template('vistas/webpay_post.html')
    return HttpResponse(template.render(context, request))

def webpay_resultado(request):
    # Handle Webpay payment result
    token_ws = request.GET.get('token_ws')
    if not token_ws:
        return HttpResponse("No se recibió token de pago.", status=400)

    transaction = Transaction()
    transaction.configure_for_integration(
        commerce_code=IntegrationCommerceCodes.WEBPAY_PLUS,
        api_key=IntegrationApiKeys.WEBPAY
    )

    result = transaction.commit(token_ws)

    # Here you can update appointment status based on result
    # For now, just display result info
    return HttpResponse(f"Resultado de pago: {result}")
