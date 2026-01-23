#!/bin/bash
# Borgo-Bot Setup & Diagnose
# Prüft alle Voraussetzungen und richtet das System ein

echo "╔════════════════════════════════════════════════╗"
echo "║   Borgo-Bot Setup & Diagnose                  ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

BORGO_DIR="/Users/svenfriess/borgobatone-04"

# ============================================
# 1. VERZEICHNIS-PRÜFUNG
# ============================================

echo "📁 Prüfe Verzeichnisse..."
echo ""

if [ ! -d "$BORGO_DIR" ]; then
    echo "❌ Borgo-Verzeichnis nicht gefunden: $BORGO_DIR"
    exit 1
else
    echo "✅ Borgo-Verzeichnis: $BORGO_DIR"
fi

cd "$BORGO_DIR" || exit 1

# Erstelle logs-Verzeichnis
if [ ! -d "logs" ]; then
    echo "📁 Erstelle logs-Verzeichnis..."
    mkdir -p logs
    echo "✅ logs/ erstellt"
else
    echo "✅ logs/ existiert"
fi

# Erstelle backups-Verzeichnis falls nicht vorhanden
if [ ! -d "backups" ]; then
    mkdir -p backups
    echo "✅ backups/ erstellt"
else
    echo "✅ backups/ existiert"
fi

echo ""

# ============================================
# 2. DATEI-PRÜFUNG
# ============================================

echo "📄 Prüfe erforderliche Dateien..."
echo ""

REQUIRED_FILES=(
    "borgo_bot_multi.py"
    "config_multi_bot.py"
    "borgo_knowledge_base.yaml"
    ".env"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file FEHLT!"
    fi
done

echo ""

# ============================================
# 3. OLLAMA-PRÜFUNG
# ============================================

echo "🤖 Prüfe Ollama..."
echo ""

if command -v ollama &> /dev/null; then
    echo "✅ Ollama installiert"
    
    if pgrep -x "ollama" > /dev/null; then
        echo "✅ Ollama läuft"
        echo ""
        echo "📦 Verfügbare Modelle:"
        ollama list | head -10
    else
        echo "⚠️  Ollama installiert aber läuft NICHT"
        echo "   Starte mit: ollama serve"
    fi
else
    echo "❌ Ollama nicht gefunden"
    echo "   Installation: https://ollama.ai"
fi

echo ""

# ============================================
# 4. SIGNAL-CLI PRÜFUNG
# ============================================

echo "📱 Prüfe Signal-CLI..."
echo ""

SIGNAL_PATHS=(
    "/opt/homebrew/bin/signal-cli"
    "/usr/local/bin/signal-cli"
    "$HOME/.local/bin/signal-cli"
)

FOUND_SIGNAL=""
for path in "${SIGNAL_PATHS[@]}"; do
    if [ -x "$path" ]; then
        echo "✅ signal-cli gefunden: $path"
        FOUND_SIGNAL="$path"
        break
    fi
done

if [ -z "$FOUND_SIGNAL" ]; then
    echo "⚠️  signal-cli nicht an Standard-Orten gefunden"
    echo "   Suche mit: which signal-cli"
else
    # Prüfe ob daemon läuft
    if pgrep -f "signal-cli.*daemon" > /dev/null; then
        echo "✅ signal-cli daemon läuft"
    else
        echo "⚠️  signal-cli daemon läuft NICHT"
    fi
fi

echo ""

# ============================================
# 5. PYTHON-UMGEBUNG
# ============================================

echo "🐍 Prüfe Python-Umgebung..."
echo ""

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION"
    
    # Prüfe wichtige Pakete
    echo ""
    echo "📦 Python-Pakete:"
    python3 -c "import yaml; print('✅ PyYAML')" 2>/dev/null || echo "❌ PyYAML fehlt (pip install pyyaml)"
    python3 -c "import requests; print('✅ requests')" 2>/dev/null || echo "❌ requests fehlt (pip install requests)"
else
    echo "❌ Python3 nicht gefunden"
fi

echo ""

# ============================================
# 6. LAUFENDE PROZESSE
# ============================================

echo "🔄 Laufende Borgo-Bot Prozesse:"
echo ""

BORGO_PROCS=$(ps aux | grep "python.*borgo" | grep -v grep)
if [ -z "$BORGO_PROCS" ]; then
    echo "ℹ️  Keine Borgo-Bot Prozesse laufen"
else
    echo "$BORGO_PROCS" | awk '{printf "  PID: %-7s | %s\n", $2, $11" "$12" "$13}'
fi

echo ""

# ============================================
# 7. ZUSAMMENFASSUNG
# ============================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Zusammenfassung"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Prüfe ob alles ready ist
READY=true

if [ ! -f "borgo_bot_multi.py" ]; then
    echo "❌ Haupt-Script fehlt"
    READY=false
fi

if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama läuft nicht"
    READY=false
fi

if [ "$READY" = true ]; then
    echo "✅ System ist bereit für Borgo-Bot!"
    echo ""
    echo "Nächster Schritt:"
    echo "  ./super_simple_restart.sh"
else
    echo "⚠️  System nicht vollständig bereit"
    echo ""
    echo "Behebe die oben genannten Probleme und führe erneut aus"
fi

echo ""
