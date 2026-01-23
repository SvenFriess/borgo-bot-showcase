# Borgo-Bot v0.97 - System-Prompt Fix

## Problem
Der Bot gibt **paraphrasierte** Antworten statt den **exakten Text** aus der Knowledge Base:

### v0.96 Verhalten (FALSCH):
```
User: "Wo finde ich das Benvenuti?"

YAML sagt:
"Das Benvenuti-Guide findest du auf der Piazza:
https://piazza.borgo-batone.com/node/819?language_content_entity=en"

Bot antwortet:
"Das Benvenuti-Guide befindet sich nicht an einer bestimmten Stelle. 
Sie erhalten es während Ihrer Ankunft..."
```

❌ Der LLM **generiert** eigenen Text statt zu kopieren!

## Ursache
**Schwacher System-Prompt** in `llm_handler.py`:
```python
"• Gib Informationen präzise wieder - nutze die Original-Formulierungen"
```

Das erlaubt dem LLM zu viel Interpretationsspielraum!

## Lösung v0.97
**Strikter System-Prompt** der WORD-FOR-WORD Reproduction erzwingt:

### Vorher (v0.96):
```python
"• Gib Informationen präzise wieder - nutze die Original-Formulierungen"
```

### Nachher (v0.97):
```python
"KRITISCHE REGEL - WORD-FOR-WORD REPRODUCTION:",
"• Kopiere Texte aus der Knowledge Base EXAKT - Wort für Wort",
"• KEINE Paraphrasierung, KEINE Umformulierung, KEINE eigenen Worte",
"• Übernimm Listen, Nummerierungen, Links GENAU wie vorgegeben"
```

---

## Installation

### Automatisch (empfohlen)

```bash
# 1. Ins Projektverzeichnis
cd ~/Projekte/borgobatone-04

# 2. Fix installieren
python3 apply_system_prompt_fix_v097.py

# 3. Bot neu starten
./start_community_bot.sh

# 4. Testen
# In Signal: !Bot Wo finde ich das Benvenuti?
```

Das Script:
- ✅ Erstellt Backups von `llm_handler.py` und `context_manager.py`
- ✅ Patcht beide Dateien mit strengeren Prompts
- ✅ Validiert die Änderungen

---

## Geänderte Dateien

### 1. `llm_handler.py`
**Funktion:** `_build_prompt()`

**Alt:**
```python
"• Nutze NUR Informationen aus der Knowledge Base unten",
"• Gib Informationen präzise wieder - nutze die Original-Formulierungen",
```

**Neu:**
```python
"KRITISCHE REGEL - WORD-FOR-WORD REPRODUCTION:",
"• Kopiere Texte aus der Knowledge Base EXAKT - Wort für Wort",
"• KEINE Paraphrasierung, KEINE Umformulierung, KEINE eigenen Worte",
```

### 2. `context_manager.py`
**Funktion:** `_format_context()`

**Alt:**
```python
"Du bist Borgo-Bot, der Borgo-Batone Gäste-Assistent.",
"Antworte NUR basierend auf folgenden Informationen:",
```

**Neu:**
```python
"Du bist Borgo-Bot, der Borgo-Batone Gäste-Assistent.",
"WICHTIG: Kopiere die Antworten unten WORT-FÜR-WORT - keine Paraphrasierung!",
"Antworte EXAKT mit dem Text aus der Knowledge Base:",
```

---

## Testing

### Test-Query
```
!Bot Wo finde ich das Benvenuti?
```

### ✅ Erwartete Antwort (v0.97):
```
Das Benvenuti-Guide findest du auf der Piazza:
https://piazza.borgo-batone.com/node/819?language_content_entity=en

Ich empfehle dir, es vor der Anreise durchzulesen!
```

### ❌ Fehlerhafte Antwort (v0.96):
```
Das Benvenuti-Guide befindet sich nicht an einer bestimmten Stelle...
[GENERIERTER TEXT]
```

### Weitere Test-Queries
```
!Bot Wie viel Mehl für Pizza?
!Bot Sind Hunde erlaubt?
!Bot WLAN Passwort?
```

Alle sollten **exakt** den Text aus der YAML wiedergeben!

---

## Rollback

Falls Probleme auftreten:

```bash
# Backups wiederherstellen
cp backups/llm_handler_backup_YYYYMMDD_HHMMSS.py llm_handler.py
cp backups/context_manager_backup_YYYYMMDD_HHMMSS.py context_manager.py

# Bot neu starten
./start_community_bot.sh
```

---

## Impact & Priorität

**Priorität:** 🔴 **KRITISCH**  
**Impact:** Alle Bot-Antworten  
**Deadline:** Vor Production-Rollout am 8.1.2026

### Warum kritisch?
- ❌ v0.96 gibt **falsche** Informationen (generiert statt zu kopieren)
- ❌ v0.96 verletzt Grundprinzip: "Word-for-Word Reproduction" (seit v0.30)
- ❌ Community-Tester bekommen inkonsistente Antworten
- ✅ v0.97 stellt sicher, dass JEDE Antwort aus der YAML stammt

---

## Deployment Plan

1. ✅ **DEV-Bot**: Fix testen
2. ✅ **TEST-Bot**: Fix validieren
3. ✅ **Community-Test-Bot**: Fix installieren (JETZT)
4. 📅 **Production-Bot**: Mit Rollout am 8.1.2026

---

## Technische Details

### Warum hat v0.96 nicht funktioniert?

Die YAML hatte den **richtigen** Text:
```yaml
answer: 'Das Benvenuti-Guide findest du auf der Piazza:
  https://piazza.borgo-batone.com/node/819?language_content_entity=en
  
  Ich empfehle dir, es vor der Anreise durchzulesen!'
```

Aber der System-Prompt war zu **schwach**:
```python
"Gib Informationen präzise wieder" 
```

Der LLM interpretierte das als: "Gib es ungefähr wieder in eigenen Worten"

### v0.97 Lösung

**Explizite** Anweisung:
```python
"KRITISCHE REGEL - WORD-FOR-WORD REPRODUCTION"
"Kopiere Texte EXAKT - Wort für Wort"
"KEINE Paraphrasierung"
```

Jetzt versteht der LLM: "Kopieren, nicht interpretieren!"

---

## Checklist

- [ ] Backup erstellt (automatisch durch Script)
- [ ] v0.97 auf Community-Test installiert
- [ ] Benvenuti-Query getestet
- [ ] 3-5 weitere Queries getestet
- [ ] Alle Antworten = exakt aus YAML
- [ ] Keine Halluzinationen
- [ ] Response-Time < 60 Sekunden
- [ ] Tester informiert über Fix
- [ ] Logs gecheckt (keine Errors)
- [ ] Production-Rollout geplant

---

**Version**: 0.97  
**Datum**: 7. Januar 2026  
**Priorität**: 🔴 Kritisch  
**Status**: Ready for Deployment  

**Kombiniert mit**: v0.96 (Benvenuti-Link-Fix)
