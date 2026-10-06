"""Django loyihangizga ulash.

1) `payme_payment/` papkasini Django loyihangizga ko'chiring.

2) urls.py ga yozing:

       from myapp.views import payme_webhook_view

       urlpatterns = [
           path("payme", payme_webhook_view),
       ]

   DIQQAT: bu manzil Payme SERVERIDAN keladi, foydalanuvchi brauzeridan
   emas — shuning uchun @csrf_exempt shart.
"""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from payme_payment import handle_request


@csrf_exempt
@require_POST
def payme_webhook_view(request: HttpRequest) -> JsonResponse:
    try:
        body = json.loads(request.body or b"{}")
    except (ValueError, TypeError):
        body = {}

    auth = request.headers.get("Authorization")
    return JsonResponse(handle_request(body, auth))


# --- To'lov havolasini yasash (o'z view'ingizda) ------------------------------
#
#   from payme_payment import checkout_url, som_to_tiyin
#
#   def checkout(request, order_id):
#       order = Order.objects.get(id=order_id, user=request.user)
#       return redirect(checkout_url({"order_id": order.id}, som_to_tiyin(order.price)))
