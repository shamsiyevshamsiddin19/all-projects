#!/usr/bin/env bash
# Har necha daqiqada userbot akkauntlarini tekshiradi.
# Biror akkaunt ishlamasa yoki qayta-qayta o'chib yonsa (ehtimol login kerak),
# Telegram bot orqali sizga ogohlantirish yuboradi.
#
# .env da kerak:
#   ALERT_BOT_TOKEN=...   (@BotFather dan)
#   ALERT_CHAT_ID=...     (sizning chat id — botga /start bosilgach aniqlanadi)

APP=/opt/telegram-userbot
ENVF="$APP/.env"
STATEF="$APP/data/monitor_restarts.txt"
mkdir -p "$APP/data"

BOT_TOKEN=$(grep '^ALERT_BOT_TOKEN=' "$ENVF" | cut -d= -f2-)
CHAT=$(grep '^ALERT_CHAT_ID=' "$ENVF" | cut -d= -f2-)

alert() {
  if [ -n "$BOT_TOKEN" ] && [ -n "$CHAT" ]; then
    curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      --data-urlencode "chat_id=${CHAT}" \
      --data-urlencode "text=$1" >/dev/null
  fi
  echo "$(date '+%F %T') ALERT: $1"
}

for a in acc1 acc2 acc3; do
  svc="userbot@$a"

  # 1) Umuman ishlamayaptimi?
  if ! systemctl is-active --quiet "$svc"; then
    alert "🔴 $svc ISHLAMAYAPTI! Serverda tekshiring."
    continue
  fi

  # 2) Qayta-qayta o'chib yonyaptimi? (ehtimol Telegram logout qildi -> login kerak)
  nr=$(systemctl show -p NRestarts --value "$svc" 2>/dev/null)
  prev=$(grep "^$a=" "$STATEF" 2>/dev/null | cut -d= -f2)
  prev=${prev:-0}
  if [ -n "$nr" ] && [ "$nr" -ge $((prev + 3)) ]; then
    alert "⚠️ $svc qayta-qayta ishga tushmoqda (restart=$nr). Ehtimol qayta login kerak."
  fi
  # holatni yangilaymiz
  if [ -f "$STATEF" ]; then sed -i "/^$a=/d" "$STATEF"; fi
  echo "$a=${nr:-0}" >> "$STATEF"
done
