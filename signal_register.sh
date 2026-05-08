#!/bin/bash
# signal_register.sh - Signal-CLI Registrierung mit Captcha-Link aus Clipboard

PHONE="+4915755901211"
SIGNAL_CLI="signal-cli"  # oder vollständiger Pfad

echo "📋 Schritt 1: Captcha lösen"
echo "👉 Öffne diese URL im Browser:"
echo "   https://signalcaptchas.org/registration/generate.html"
echo ""
echo "⏳ Löse das Captcha und warte auf den Link im Browser..."
echo "   Der Link beginnt mit: signalcaptcha://"
echo ""
echo "📋 Kopiere den Link in den Zwischenspeicher (Cmd+C / Ctrl+C)"
echo ""
read -p "✅ Drücke ENTER wenn der Link kopiert ist..."

# Link aus Clipboard holen
if command -v pbpaste &>/dev/null; then
    # macOS
    CAPTCHA_LINK=$(pbpaste)
elif command -v xclip &>/dev/null; then
    # Linux mit xclip
    CAPTCHA_LINK=$(xclip -selection clipboard -o)
elif command -v xsel &>/dev/null; then
    # Linux mit xsel
    CAPTCHA_LINK=$(xsel --clipboard --output)
else
    echo "❌ Kein Clipboard-Tool gefunden!"
    echo "   Installiere xclip: sudo apt install xclip"
    exit 1
fi

# Validierung
if [[ -z "$CAPTCHA_LINK" ]]; then
    echo "❌ Clipboard ist leer!"
    exit 1
fi

if [[ "$CAPTCHA_LINK" != signalcaptcha://* ]]; then
    echo "❌ Link sieht falsch aus: $CAPTCHA_LINK"
    echo "   Erwartet wird: signalcaptcha://..."
    exit 1
fi

echo ""
echo "✅ Captcha-Link gefunden:"
echo "   ${CAPTCHA_LINK:0:60}..."  # Erste 60 Zeichen anzeigen
echo ""

# Registrierung starten
echo "📱 Schritt 2: Registrierung mit Signal..."
$SIGNAL_CLI -a "$PHONE" register --captcha "$CAPTCHA_LINK"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Registrierungsanfrage gesendet!"
    echo "📲 Du bekommst eine SMS mit dem Verifizierungs-Code..."
    echo ""
    
    # Verifizierung
    read -p "🔢 Gib den SMS-Code ein (Format: 123-456): " SMS_CODE
    SMS_CODE=$(echo "$SMS_CODE" | tr -d '-')  # Bindestrich entfernen
    
    $SIGNAL_CLI -a "$PHONE" verify "$SMS_CODE"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Signal-CLI erfolgreich registriert!"
        echo "   Account: $PHONE"
    else
        echo "❌ Verifizierung fehlgeschlagen. Code nochmal prüfen."
    fi
else
    echo "❌ Registrierung fehlgeschlagen."
    echo "   Tipp: Captcha neu lösen und Script nochmal starten."
fi