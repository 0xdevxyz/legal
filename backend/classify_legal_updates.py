#!/usr/bin/env python3
"""
Script zur automatischen KI-Klassifizierung aller legal_updates
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime
import json

# OpenRouter API
import httpx

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')

async def classify_update_with_ai(update: dict) -> dict:
    """Klassifiziert ein Legal Update mit der AI"""
    
    prompt = f"""Analysiere diese Gesetzesänderung und klassifiziere sie:

Titel: {update['title']}
Beschreibung: {update['description']}
Typ: {update['update_type']}
Schwere: {update['severity']}

Antworte im JSON-Format:
{{
    "action_required": true/false,
    "confidence": "high"/"medium"/"low",
    "impact_score": 1-10,
    "primary_action_type": "scan_website"/"update_cookie_banner"/"review_policy"/"contact_support"/"info_only",
    "primary_button_text": "Konkrete Aktion (max 30 Zeichen)",
    "primary_button_color": "red"/"orange"/"blue"/"green"/"gray",
    "primary_button_icon": "🔍"/"🍪"/"📄"/"💬"/"ℹ️",
    "reasoning": "Kurze Begründung (max 200 Zeichen)",
    "user_impact": "Was bedeutet das für den Nutzer? (max 150 Zeichen)"
}}

Wichtig:
- action_required=true nur wenn der Nutzer JETZT handeln muss
- impact_score: 8-10=kritisch, 5-7=wichtig, 1-4=informativ
- button_text muss eine konkrete Handlungsaufforderung sein
- button_color: red=dringend, orange=wichtig, blue=empfohlen, gray=info
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4-turbo",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extrahiere JSON aus der Antwort
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    classification = json.loads(json_match.group())
                    return classification
                else:
                    print(f"❌ Kein JSON in AI-Antwort gefunden")
                    return None
            else:
                print(f"❌ OpenRouter API Error: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Error calling AI: {e}")
        return None


async def main():
    """Hauptfunktion"""
    
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY nicht gesetzt!")
        sys.exit(1)
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL nicht gesetzt!")
        sys.exit(1)
    
    print("🚀 Starte KI-Klassifizierung...")
    
    # Verbinde zur Datenbank
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Hole alle legal_updates ohne Klassifizierung
        updates = await conn.fetch("""
            SELECT lu.id, lu.title, lu.description, lu.update_type, lu.severity, lu.url
            FROM legal_updates lu
            LEFT JOIN ai_classifications ac ON lu.id::varchar = ac.update_id::varchar
            WHERE ac.id IS NULL
            ORDER BY lu.published_at DESC
        """)
        
        print(f"📊 Gefunden: {len(updates)} unklassifizierte Updates")
        
        for idx, update in enumerate(updates, 1):
            print(f"\n[{idx}/{len(updates)}] Klassifiziere: {update['title'][:50]}...")
            
            # Klassifiziere mit AI
            classification = await classify_update_with_ai(dict(update))
            
            if classification:
                # Speichere in Datenbank (mit allen Pflichtfeldern)
                await conn.execute("""
                    INSERT INTO ai_classifications (
                        update_id, user_id,
                        action_required, confidence, severity, impact_score,
                        primary_action_type, primary_action_priority, primary_action_title, primary_action_description,
                        primary_button_text, primary_button_color, primary_button_icon,
                        reasoning, user_impact,
                        classified_at
                    ) VALUES ($1, NULL, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """,
                    str(update['id']),
                    classification.get('action_required', True),
                    classification.get('confidence', 'medium'),
                    update['severity'],  # Nutze severity vom Update
                    float(classification.get('impact_score', 5.0)),
                    classification.get('primary_action_type', 'scan_website'),
                    1,  # priority
                    classification.get('primary_button_text', 'Jetzt prüfen'),
                    classification.get('user_impact', 'Gesetzesänderung'),
                    classification.get('primary_button_text', 'Jetzt prüfen'),
                    classification.get('primary_button_color', 'blue'),
                    classification.get('primary_button_icon', '🔍'),
                    classification.get('reasoning', 'KI-Klassifizierung'),
                    classification.get('user_impact', 'Gesetzesänderung'),
                    datetime.utcnow()
                )
                
                print(f"   ✅ {classification.get('primary_button_icon', '🔍')} "
                      f"action={classification.get('action_required', False)}, "
                      f"impact={classification.get('impact_score', 5)}, "
                      f"button=\"{classification.get('primary_button_text', 'Prüfen')}\"")
            else:
                print(f"   ⚠️ Klassifizierung fehlgeschlagen, überspringe")
            
            # Kleine Pause um Rate-Limits zu vermeiden
            await asyncio.sleep(2)
        
        print(f"\n🎉 Fertig! {len(updates)} Updates klassifiziert")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

