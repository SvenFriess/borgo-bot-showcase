#!/usr/bin/env python3
"""
Update config_multi_bot.py mit v3.71 Features - Einfache Version
"""

# Lese die aktuelle config_multi_bot.py
with open('config_multi_bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Update QUICK_RESPONSES mit Version
old_quick = '''QUICK_RESPONSES = {
    "ping": "pong",
    "test": "Borgo-Bot läuft.",
    "status": "Borgo-Bot online und bereit.",
}'''

new_quick = '''QUICK_RESPONSES = {
    "ping": "pong",
    "test": f"Borgo-Bot v{BOT_VERSION} läuft.",
    "status": f"Borgo-Bot v{BOT_VERSION} online und bereit.",
    "version": f"Borgo-Bot v{BOT_VERSION}",
}'''

if old_quick in content:
    content = content.replace(old_quick, new_quick)
    changes_made.append("✅ QUICK_RESPONSES mit Version aktualisiert")
else:
    print("⚠️  QUICK_RESPONSES bereits aktualisiert oder nicht gefunden")

# 2. Füge META_QUERY_PATTERNS hinzu
if 'META_QUERY_PATTERNS' not in content:
    meta_section = """
# Meta/Playful Queries (questions about the bot itself, not Borgo topics)
META_QUERY_PATTERNS = [
    r'\\bferien\\b',
    r'\\burlaub\\b',
    r'\\bpause\\b',
    r'\\bfrei\\s+(haben|machen)\\b',
    r'\\bschlafen\\b',
    r'\\bmüde\\b',
    r'\\bausruhen\\b',
    r'\\bwochenende\\b',
    r'\\bfreizeit\\b',
]
"""
    # Suche QUICK_RESPONSES und füge danach ein
    quick_pos = content.find('QUICK_RESPONSES = {')
    if quick_pos > 0:
        # Finde das Ende von QUICK_RESPONSES
        end_pos = content.find('}', quick_pos) + 1
        # Füge nach dem nächsten Newline ein
        insert_pos = content.find('\n', end_pos) + 1
        content = content[:insert_pos] + meta_section + content[insert_pos:]
        changes_made.append("✅ META_QUERY_PATTERNS hinzugefügt")

# 3. Erweitere FORBIDDEN_PHRASES
if 'Ich mache Ferien nicht' not in content:
    old_forbidden = '    "Ich bin Claude",'
    new_forbidden = '''    "Ich bin Claude",
    "Ich bin Mistral",
    "Ich bin ein AI",
    "künstliche Intelligenz",
    "Ich mache Ferien nicht",
    "Ich mache keine Ferien",'''
    
    if old_forbidden in content:
        content = content.replace(old_forbidden, new_forbidden)
        changes_made.append("✅ FORBIDDEN_PHRASES erweitert")

# 4. Füge meta_query Fallback hinzu
if "'meta_query':" not in content:
    # Finde die Position nach 'no_keywords'
    no_keywords_pos = content.find("'no_keywords':")
    if no_keywords_pos > 0:
        # Finde das Ende dieses Eintrags (nächstes """,)
        end_pos = content.find('""",', no_keywords_pos) + 4
        
        meta_fallback = """
    
    'meta_query': \"\"\"Ich bin 24/7 für euch da! 🤖

Für Borgo-Fragen stehe ich immer zur Verfügung. Stelle mir gerne eine konkrete Frage zu:
• Einrichtungen (Pizzaofen, Pools, WLAN)
• Hausregeln und Check-in/out
• Notfälle und Sicherheit\"\"\","""
        
        content = content[:end_pos] + meta_fallback + content[end_pos:]
        changes_made.append("✅ meta_query Fallback hinzugefügt")

# 5. Erweitere HALLUCINATION_PATTERNS
if 'Spezifischer Zahlencode' not in content:
    # Finde HALLUCINATION_PATTERNS
    hall_start = content.find('HALLUCINATION_PATTERNS = [')
    if hall_start > 0:
        # Finde die erste Zeile nach [
        first_newline = content.find('\n', hall_start)
        
        new_patterns = """    # Erfundene spezifische Details (KRITISCH!)
    (r'\\bCode\\s+\\d{4,}\\b', 'Spezifischer Zahlencode (wahrscheinlich erfunden)'),
    (r'\\bTresor.*Code\\b', 'Tresor-Code Details (nicht verifiziert)'),
    (r'\\b\\d{1,2}:\\d{2}\\s*Uhr\\b', 'Spezifische Uhrzeit (möglicherweise erfunden)'),
    (r'\\bZimmer\\s+\\d+\\b', 'Spezifische Zimmernummer (möglicherweise erfunden)'),
    (r'\\bTelefon:?\\s*\\+?\\d{6,}', 'Spezifische Telefonnummer (möglicherweise erfunden)'),
    
"""
        content = content[:first_newline+1] + new_patterns + content[first_newline+1:]
        changes_made.append("✅ HALLUCINATION_PATTERNS erweitert")

# 6. Füge is_meta_query() Funktion hinzu
if 'def is_meta_query' not in content:
    meta_function = '''

def is_meta_query(text):
    """
    Prüft ob eine Frage über den Bot selbst ist (Ferien, Müdigkeit, etc.)
    statt über Borgo-Themen.
    
    Returns:
        bool: True wenn Meta-Query erkannt wurde
    """
    import re
    text_lower = text.lower()
    
    for pattern in META_QUERY_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

'''
    # Finde die HILFSFUNKTIONEN Section
    helper_pos = content.find('# HILFSFUNKTIONEN')
    if helper_pos > 0:
        # Finde das Ende der Kommentarzeile
        end_of_line = content.find('\n', helper_pos)
        content = content[:end_of_line] + meta_function + content[end_of_line:]
        changes_made.append("✅ is_meta_query() Funktion hinzugefügt")

# Schreibe die aktualisierte Config
with open('config_multi_bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*70)
print("🎉 config_multi_bot.py wurde aktualisiert!")
print("="*70)

if changes_made:
    print("\nVorgenommene Änderungen:")
    for change in changes_made:
        print(f"  {change}")
else:
    print("\n⚠️  Keine Änderungen nötig - bereits aktualisiert")

print("\n" + "="*70)
