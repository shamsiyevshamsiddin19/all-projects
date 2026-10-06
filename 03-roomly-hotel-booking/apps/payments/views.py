import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .gateways import click


@csrf_exempt
@require_POST
def click_webhook(request):
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        # Click POST qiladi application/x-www-form-urlencoded ham qilishi mumkin
        data = request.POST.dict()

    action = str(data.get("action"))
    try:
        if action == str(click.ACTION_PREPARE):
            result = click.prepare(data)
        elif action == str(click.ACTION_COMPLETE):
            result = click.complete(data)
        else:
            result = {"error": click.ERROR_TRANS_NOT_FOUND, "error_note": "Unknown action"}
    except click.ClickError as exc:
        result = {"error": exc.code, "error_note": exc.note}

    return JsonResponse(result)
