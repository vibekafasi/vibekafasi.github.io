#!/usr/bin/env bash
# VIBE KAFASI — DIŞ NÖBET (2026-11-11). GitHub'ın bilgisayarında çalışır: sunucu TAMAMEN kapansa bile haber gelir.
# Siteye bakar; 2 denemede de cevap yoksa (ya da 5xx) fabrika botundan Serdar'a yazar. Kapalı kaldıkça saatte bir hatırlatır, açılınca "düzeldi" der.
# SSL sertifikası 7 günden az kaldıysa günde bir uyarır. Gizli bilgi tutmaz: anahtar GitHub "Secrets" içinde.
# Ortam: TG_TOKEN, TG_CHAT (zorunlu) · HEDEF_URL (varsayılan https://fabrika.lorusseos.com) · DURUM_DOSYA · TG_API · TEKRAR_BEKLE
set -u
URL=${HEDEF_URL:-https://fabrika.lorusseos.com}; D=${DURUM_DOSYA:-.durum/durum.txt}; API=${TG_API:-https://api.telegram.org}
mkdir -p "$(dirname "$D")"
[ -n "${TG_TOKEN:-}" ] && [ -n "${TG_CHAT:-}" ] || { echo "TG_TOKEN / TG_CHAT eksik (GitHub → Settings → Secrets)"; exit 1; }
dene() { curl -sS -o /dev/null -w '%{http_code}' --max-time 25 -L "$URL" 2>/dev/null || true; }
dusuk_mu() { [ -z "$1" ] || [ "$1" = 000 ] || [ "$1" -ge 500 ] 2>/dev/null; }
gonder() { curl -sS -o /dev/null --max-time 20 -X POST "$API/bot$TG_TOKEN/sendMessage" -d chat_id="$TG_CHAT" --data-urlencode text="$1" || echo "Telegram'a gönderilemedi"; }
K=$(dene)
if dusuk_mu "$K"; then sleep "${TEKRAR_BEKLE:-60}"; K=$(dene); fi
read -r ESKI ESKI_T SSL_T < "$D" 2>/dev/null || { ESKI=ok; ESKI_T=0; SSL_T=0; }
SIMDI=$(date +%s)
if dusuk_mu "$K"; then
  if [ "$ESKI" != dusuk ] || [ $((SIMDI - ESKI_T)) -ge 3600 ]; then
    gonder "🚨 DIŞ NÖBET: $URL cevap vermiyor (kod ${K:-000}).
Sunucu tamamen kapanmış ya da internetten kopmuş olabilir; sunucunun içindeki KORUMA da bu yüzden haber veremiyor olabilir.
Ne yap: hosting panelinden sunucunun açık olduğuna bak (gerekirse yeniden başlat), sonra Claude'a söyle."
    ESKI_T=$SIMDI
  fi
  echo "dusuk $ESKI_T ${SSL_T:-0}" > "$D"; echo "DÜŞÜK ($K)"
else
  [ "$ESKI" = dusuk ] && gonder "✅ DIŞ NÖBET: $URL yine cevap veriyor (kod $K)."
  echo "ok $SIMDI ${SSL_T:-0}" > "$D"; echo "AYAKTA ($K)"
fi
case "$URL" in https://*)
  H=${URL#https://}; H=${H%%/*}
  BIT=$(echo | timeout 20 openssl s_client -servername "$H" -connect "$H:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  if [ -n "$BIT" ]; then
    GUN=$(( ($(date -d "$BIT" +%s) - SIMDI) / 86400 ))
    if [ "$GUN" -lt 7 ] && [ $((SIMDI - ${SSL_T:-0})) -ge 86400 ]; then
      gonder "🔒 DIŞ NÖBET: $H SSL sertifikasının bitmesine $GUN gün kaldı. Claude'a söyle."
      read -r A1 A2 _ < "$D"; echo "$A1 $A2 $SIMDI" > "$D"
    fi
  fi;;
esac
exit 0
