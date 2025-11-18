#!/usr/bin/env python3
"""
Regelbasierte Klassifizierung von legal_updates
(Fallback ohne AI)
"""

import asyncio
import asyncpg
import os
import sys
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', '')


def classify_by_rules(update: dict) -> dict:
    """Regelbasierte Klassifizierung basierend auf update_type und severity"""
    
    update_type = update['update_type']
    severity = update['severity']
    title = update['title'].lower()
    
    # Standard-Werte
    classification = {
        'action_required': False,
        'confidence': 'medium',
        'impact_score': 5.0,
        'primary_action_type': 'info_only',
        'primary_button_text': 'Mehr erfahren',
        'primary_button_color': 'gray',
        'primary_button_icon': 'ℹ️',
        'reasoning': 'Informativ - Keine sofortige Aktion erforderlich',
        'user_impact': 'Informative Gesetzesänderung'
    }
    
    # === CRITICAL ===
    if severity == 'critical':
        classification.update({
            'action_required': True,
            'confidence': 'high',
            'impact_score': 9.0,
            'primary_button_color': 'red',
        })
        
        if 'cookie' in title or 'consent' in title:
            classification.update({
                'primary_action_type': 'update_cookie_banner',
                'primary_button_text': 'Cookie-Banner aktualisieren',
                'primary_button_icon': '🍪',
                'reasoning': 'Kritisch: Cookie-Einwilligung muss angepasst werden',
                'user_impact': 'Rechtliche Anpassung notwendig - Bußgeldrisiko'
            })
        elif 'impressum' in title:
            classification.update({
                'primary_action_type': 'review_policy',
                'primary_button_text': 'Impressum prüfen',
                'primary_button_icon': '📄',
                'reasoning': 'Kritisch: Impressum muss aktualisiert werden',
                'user_impact': 'Pflichtangaben fehlen - Abmahnrisiko'
            })
        else:
            classification.update({
                'primary_action_type': 'scan_website',
                'primary_button_text': 'Website jetzt scannen',
                'primary_button_icon': '🔍',
                'reasoning': 'Kritisch: Dringende Überprüfung erforderlich',
                'user_impact': 'Hohe Dringlichkeit - Sofortiges Handeln nötig'
            })
    
    # === HIGH ===
    elif severity == 'high':
        classification.update({
            'action_required': True,
            'confidence': 'high',
            'impact_score': 7.0,
            'primary_button_color': 'orange',
        })
        
        if 'datenschutz' in title or 'dsgvo' in title or 'privacy' in title:
            classification.update({
                'primary_action_type': 'review_policy',
                'primary_button_text': 'Datenschutzerklärung prüfen',
                'primary_button_icon': '📄',
                'reasoning': 'Wichtig: Datenschutzerklärung sollte überprüft werden',
                'user_impact': 'Anpassung empfohlen für DSGVO-Konformität'
            })
        elif 'barriere' in title or 'accessibility' in title:
            classification.update({
                'primary_action_type': 'scan_website',
                'primary_button_text': 'Barrierefreiheit prüfen',
                'primary_button_icon': '♿',
                'reasoning': 'Wichtig: Barrierefreiheitsanforderungen prüfen',
                'user_impact': 'Gesetzliche Anforderungen ab 2025'
            })
        else:
            classification.update({
                'primary_action_type': 'scan_website',
                'primary_button_text': 'Compliance prüfen',
                'primary_button_icon': '🔍',
                'reasoning': 'Wichtig: Überprüfung wird empfohlen',
                'user_impact': 'Anpassung in den nächsten Wochen empfohlen'
            })
    
    # === MEDIUM ===
    elif severity == 'medium':
        classification.update({
            'action_required': True,
            'confidence': 'medium',
            'impact_score': 5.0,
            'primary_button_color': 'blue',
            'primary_action_type': 'scan_website',
            'primary_button_text': 'Jetzt überprüfen',
            'primary_button_icon': '🔍',
            'reasoning': 'Mittlere Priorität - Überprüfung empfohlen',
            'user_impact': 'Anpassung mittelfristig sinnvoll'
        })
    
    # === LOW ===
    else:  # low
        classification.update({
            'action_required': False,
            'confidence': 'high',
            'impact_score': 2.0,
            'primary_button_color': 'gray',
            'primary_action_type': 'info_only',
            'primary_button_text': 'Details ansehen',
            'primary_button_icon': 'ℹ️',
            'reasoning': 'Niedrige Priorität - Zur Kenntnis nehmen',
            'user_impact': 'Informativ - Keine Aktion erforderlich'
        })
    
    # === UPDATE_TYPE Anpassungen ===
    if update_type == 'court_ruling':
        classification['reasoning'] = 'Gerichtsurteil: ' + classification['reasoning']
    elif update_type == 'new_law':
        classification['reasoning'] = 'Neues Gesetz: ' + classification['reasoning']
    elif update_type == 'enforcement':
        classification['reasoning'] = 'Durchsetzung: ' + classification['reasoning']
    
    return classification


async def main():
    """Hauptfunktion"""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL nicht gesetzt!")
        sys.exit(1)
    
    print("🚀 Starte regelbasierte Klassifizierung...")
    
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
            print(f"\n[{idx}/{len(updates)}] Klassifiziere: {update['title'][:60]}...")
            
            # Regelbasierte Klassifizierung
            classification = classify_by_rules(dict(update))
            
            # Speichere in Datenbank
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
                classification['action_required'],
                classification['confidence'],
                update['severity'],  # Nutze severity vom Update
                float(classification['impact_score']),
                classification['primary_action_type'],
                1,  # priority
                classification['primary_button_text'],  # title
                classification['user_impact'],  # description
                classification['primary_button_text'],
                classification['primary_button_color'],
                classification['primary_button_icon'],
                classification['reasoning'],
                classification['user_impact'],
                datetime.utcnow()
            )
            
            print(f"   ✅ {classification['primary_button_icon']} "
                  f"action={classification['action_required']}, "
                  f"impact={classification['impact_score']}, "
                  f"button=\"{classification['primary_button_text']}\"")
        
        print(f"\n🎉 Fertig! {len(updates)} Updates klassifiziert")
        
        # Zeige Zusammenfassung
        summary = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE action_required = true) as action_required,
                AVG(impact_score) as avg_impact
            FROM ai_classifications
        """)
        
        print(f"\n📊 Zusammenfassung:")
        print(f"   Gesamt: {summary['total']}")
        print(f"   Aktion erforderlich: {summary['action_required']}")
        print(f"   Durchschnittlicher Impact: {summary['avg_impact']:.1f}/10")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

