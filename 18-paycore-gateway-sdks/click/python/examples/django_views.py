"""Django loyihangizga ulash.

1) `click_payment/` papkasini Django loyihangizga ko'chiring.

2) `click_payment/click_orders.py` da o'z modelingizni ulang (fayl oxiridagi
   Django ORM namunasiga qarang).

3) Quyidagi view'larni loyihangizga qo'shing (masalan `payments/views.py`).

4) urls.py ga yozing:

       from payments.views import click_prepare_view, click_complete_view

       urlpatterns = [
           path("click/prepare",  click_prepare_view),
           path("click/complete", click_complete_view),
       ]

   DIQQAT: bu ikkalasi Click SERVERIDAN keladi, foydalanuvchi brauzeridan
   emas — shuning uchun @csrf_exempt shart.
"""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from click_payment import handle_complete, handle_prepare


def _request_data(request: HttpRequest) -> dict:
    """Click so'rovidan maydonlarni oladi (form -> JSON)."""
    if request.POST:
        return request.POST.dict()

    try:
        body = json.loads(request.body or b"{}")
        if isinstance(body, dict):
            return body
    except (ValueError, TypeError):
        pass

    return request.GET.dict()


@csrf_exempt
@require_POST
def click_prepare_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(handle_prepare(_request_data(request)))


@csrf_exempt
@require_POST
def click_complete_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(handle_complete(_request_data(request)))


# --- To'lov havolasini yasash (o'z view'ingizda) ------------------------------
#
#   from click_payment import payment_url
#
#   def checkout(request, order_id):
#       order = Order.objects.get(id=order_id, user=request.user)
#       # buyurtmangizga unikal merchant_trans_id bering:
#       if not order.merchant_trans_id:
#           order.merchant_trans_id = f"ORD{order.id}"
#           order.save(update_fields=["merchant_trans_id"])
#
#       return redirect(payment_url(order.merchant_trans_id, order.price))
