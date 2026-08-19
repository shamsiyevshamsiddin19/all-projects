#!/bin/bash
# tatulmsbot self-healing watchdog.
# Health-endpoint (event-loop tirikligini bildiradi) 2 marta javob bermasa -> restart.
URL="http://127.0.0.1:8093/tatulms/health"

check() { curl -fsS -m 8 -o /dev/null "$URL"; }

# 1-urinish
if check; then exit 0; fi
# qisqa kutib 2-urinish (vaqtinchalik CPU spike'da behuda restart qilmaslik uchun)
sleep 6
if check; then exit 0; fi

logger -t tatulms-watchdog "health 2 marta javob bermadi — tatulmsbot restart qilinmoqda"
systemctl restart tatulmsbot
