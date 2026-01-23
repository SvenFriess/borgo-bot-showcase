# Borgo-Bot v0.96 - Benvenuti Link Fix

## Problem
Der Bot gibt falsche/veraltete Informationen zum Benvenuti-Guide:
- ❌ "in deiner Buchungsbestätigung"
- ❌ "Link wird bei Buchung verschickt"

## Lösung
Korrekter Piazza-Link:
```
https://piazza.borgo-batone.com/node/819?language_content_entity=en
```

---

## Installation

### Methode 1: Automatisch (empfohlen)

```bash
# 1. Script ausführbar machen
chmod +x apply_benvenuti_fix.py

# 2. Fix installieren
python3 apply_benvenuti_fix.py

# 3. Bot neu starten
# (je nach deinem Setup, z.B. systemctl restart borgo-bot)
```

Das Script:
- ✅ Erstellt automatisch Backup
- ✅ Entfernt alte Benvenuti-Einträge
- ✅ Fügt korrigierten Eintrag ein
- ✅ Validiert die Änderungen

### Methode 2: Manuell

```bash
# 1. Backup erstellen
cp borgo_knowledge_base.yaml borgo_knowledge_base.yaml.backup

# 2. Alte benvenuti Einträge in YAML löschen

# 3. Inhalt von benvenuti_link_fix_v096.yaml einfügen

# 4. Bot neu starten
```

---

## Testing

### Test-Queries
Nach der Installation sollten diese Fragen korrekt beantwortet werden:

```
User: "Wo finde ich das Benvenuti?"
Bot: ✅ Sollte Piazza-Link enthalten

User: "Wo ist der Guest Guide?"
Bot: ✅ Sollte Piazza-Link enthalten

User: "Benvenuti Guide Link?"
Bot: ✅ Sollte Piazza-Link enthalten

User: "Gästehandbuch?"
Bot: ✅ Sollte Piazza-Link enthalten
```

### Erwartete Antwort
```
Das Benvenuti-Guide findest du auf der Piazza:
https://piazza.borgo-batone.com/node/819?language_content_entity=en

Ich empfehle dir, es vor der Anreise durchzulesen!
```

### Was NICHT mehr vorkommen sollte
- ❌ "Buchungsbestätigung"
- ❌ "wird bei Buchung verschickt"
- ❌ Andere/falsche Links

---

## Rollback

Falls Probleme auftreten:

```bash
# Backup wiederherstellen
cp backups/borgo_kb_backup_YYYYMMDD_HHMMSS.yaml borgo_knowledge_base.yaml

# Bot neu starten
```

---

## Deployment Plan

### Vor Community-Rollout (8.1.2026)

1. ✅ **DEV-Bot**: Fix installieren & testen
2. ✅ **TEST-Bot**: Fix installieren & testen
3. ✅ **Community-Test-Bot**: Fix installieren
4. 📅 **Production-Bot**: Am 8.1.2026 mit Full Rollout

### Checklist

- [ ] Backup erstellt
- [ ] Fix auf DEV getestet
- [ ] Fix auf TEST getestet
- [ ] Fix auf Community-Test installiert
- [ ] Tester informiert (neue Test-Queries)
- [ ] Alle Test-Queries funktionieren
- [ ] Keine Halluzinationen erkannt
- [ ] Response-Time < 60 Sekunden
- [ ] Production-Rollout geplant

---

## Dateien in diesem Fix

1. **benvenuti_link_fix_v096.yaml** - YAML-Einträge zum Einfügen
2. **apply_benvenuti_fix.py** - Automatisches Installations-Script
3. **README_v096_FIX.md** - Diese Anleitung

---

## Support

Bei Fragen oder Problemen:
- Logs checken: `borgo_bot_v3_5.log`
- Backup wiederherstellen (siehe oben)
- Community-Tester um Feedback bitten

---

**Version**: 0.96  
**Datum**: 7. Januar 2026  
**Priorität**: Hoch (vor Production-Rollout am 8.1.2026)  
**Impact**: Alle User, die nach Benvenuti-Guide fragen
