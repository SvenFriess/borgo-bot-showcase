#!/usr/bin/env python3
"""
Update config_multi_bot.py mit v3.71 Features
"""

import re

# Lese die aktuelle config_multi_bot.py
with open('config_multi_bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

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

content = content.replace(old_quick, new_quick)

# 2. Füge META_QUERY_PATTERNS hinzu (nach INVALID_INPUT_PATTERNS)
if 'META_QUERY_PATTERNS' not in content:
    meta_query_section = r'''
# Meta/Playful Queries (questions about the bot itself, not Borgo topics)
META_QUERY_PATTERNS = [
    r'\bferien\b',
    r'\burlaub\b',
    r'\bpause\b',
    r'\bfrei\s+(haben|machen)\b',
    r'\bschlafen\b',
    r'\bmüde\b',
    r'\bausruhen\b',
    r'\bwochenende\b',
    r'\bfreizeit\b',
]
'''
    # Füge nach INVALID_INPUT_PATTERNS ein
    pattern = r'(INVALID_INPUT_PATTERNS = \[.*?\])'
    replacement = r'\1\n' + meta_query_section
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 3. Erweitere HALLUCINATION_PATTERNS
if 'Spezifischer Zahlencode' not in content:
    # Finde HALLUCINATION_PATTERNS
    old_hall_start = content.find('HALLUCINATION_PATTERNS = [')
    if old_hall_start > 0:
        # Füge neue Patterns hinzu
        new_patterns = r'''
    # Erfundene spezifische Details (KRITISCH!)
    (r'\bCode\s+\d{4,}\b', 'Spezifischer Zahlencode (wahrscheinlich erfunden)'),
    (r'\bTresor.*Code\b', 'Tresor-Code Details (nicht verifiziert)'),
    (r'\b\d{1,2}:\d{2}\s*Uhr\b', 'Spezifische Uhrzeit (möglicherweise erfunden)'),
    (r'\bZimmer\s+\d+\b', 'Spezifische Zimmernummer (möglicherweise erfunden)'),
    (r'\bTelefon:?\s*\+?\d{6,}', 'Spezifische Telefonnummer (möglicherweise erfunden)'),
'''
        # Finde die Position nach der ersten Zeile von HALLUCINATION_PATTERNS
        insert_pos = content.find('\n', old_hall_start) + 1
        # Finde das erste Pattern
        first_pattern_pos = content.find('(r', insert_pos)
        if first_pattern_pos > 0:
            content = content[:first_pattern_pos] + new_patterns + '    ' + content[first_pattern_pos:]

# 4. Erweitere FORBIDDEN_PHRASES
if 'Ich mache Ferien nicht' not in content:
    old_forbidden = '"Ich bin Claude",'
    new_forbidden = '''"Ich bin Claude",
    "Ich bin Mistral",
    "Ich bin ein AI",
    "künstliche Intelligenz",
    "Ich mache Ferien nicht",  # Robotic phrasing
    "Ich mache keine Ferien",  # Robotic phrasing'''
    content = content.replace(old_forbidden, new_forbidden)

# 5. Füge meta_query Fallback hinzu
if "'meta_query':" not in content:
    meta_fallback = """
    'meta_query': \"\"\"Ich bin 24/7 für euch da! 🤖

Für Borgo-Fragen stehe ich immer zur Verfügung. Stelle mir gerne eine konkrete Frage zu:
• Einrichtungen (Pizzaofen, Pools, WLAN)
• Hausregeln und Check-in/out
• Notfälle und Sicherheit\"\"\",
"""
    # Füge nach 'no_keywords' ein
    pattern = r"('no_keywords':.*?\"\"\",)"
    content = re.sub(pattern, r'\1' + meta_fallback, content, flags=re.DOTALL)

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
    # Füge vor get_feature_status() ein (oder am Ende der Hilfsfunktionen)
    if 'def get_feature_status' in content:
        content = content.replace('def get_feature_status', meta_function + '\ndef get_feature_status')
    else:
        # Am Ende vor dem __main__ Block
        main_pos = content.find('if __name__ == "__main__"')
        if main_pos > 0:
            content = content[:main_pos] + meta_function + '\n' + content[main_pos:]

# Schreibe die aktualisierte Config
with open('config_multi_bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ config_multi_bot.py wurde mit v3.71 Features aktualisiert!")
print("\nHinzugefügt:")
print("  • META_QUERY_PATTERNS (Ferien-Fragen)")
print("  • QUICK_RESPONSES mit Version")
print("  • Erweiterte HALLUCINATION_PATTERNS (Code, Uhrzeiten, etc.)")
print("  • Erweiterte FORBIDDEN_PHRASES")
print("  • meta_query Fallback Response")
print("  • is_meta_query() Funktion")
