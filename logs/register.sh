# 1. Browser öffnen
open "https://signalcaptchas.org/registration/generate.html"

echo "Captcha lösen, dann Rechtsklick auf 'Open Signal' → Link kopieren"
echo "Drücke ENTER wenn bereit..."
read

# 2. Aus Clipboard lesen und registrieren
CAPTCHA=$(pbpaste)
signal-cli -a +4915755901211 register --captcha "$CAPTCHA"