import asyncio
import asyncpg
import os
import json
from datetime import datetime
import sys
sys.path.insert(0, '/app')

from ai_legal_classifier import AILegalClassifier

async def classify_new_updates():
    """Klassifiziere alle Updates die noch keine AI-Classification haben"""
    
    conn = await asyncpg.connect(os.getenv('DATABASE_URL', 'postgresql://complyo_user:YpjCMdN2024!@postgres:5432/complyo_db'))
    
    # Finde Updates ohne Classification
    unclassified = await conn.fetch('''
        SELECT lu.id, lu.update_type, lu.title, lu.description, lu.severity, 
               lu.action_required, lu.published_date, lu.effective_date, lu.url
        FROM legal_updates lu
        LEFT JOIN ai_classifications ac ON lu.id = ac.update_id
        WHERE ac.id IS NULL
        ORDER BY lu.published_date DESC
    ''')
    
    print(f"🔍 Gefunden: {len(unclassified)} Updates ohne KI-Klassifizierung\n")
    
    if not unclassified:
        print("✅ Alle Updates bereits klassifiziert!")
        await conn.close()
        return
    
    # Initialisiere AI Classifier
    classifier = AILegalClassifier()
    
    for update in unclassified:
        print(f"🤖 Klassifiziere: {update['title'][:60]}...")
        
        try:
            # Baue Update-Daten Objekt
            update_data = {
                'title': update['title'],
                'update_type': update['update_type'],
                'description': update['description'] or '',
                'severity': update['severity'],
                'published_at': str(update['published_date']),
                'effective_date': str(update['effective_date']) if update['effective_date'] else None,
                'source': update['url']
            }
            
            # Klassifizierung durchführen
            classification = await classifier.classify_legal_update(update_data)
            
            # In DB speichern
            await conn.execute('''
                INSERT INTO ai_classifications (
                    update_id, action_required, confidence, impact_score,
                    primary_action, recommended_actions, reasoning,
                    user_impact, consequences_if_ignored, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ''', 
                update['id'],
                classification.action_required,
                classification.confidence.value,
                classification.impact_score,
                json.dumps(classification.primary_action.to_dict()),
                json.dumps([a.to_dict() for a in classification.recommended_actions]),
                classification.reasoning,
                classification.user_impact,
                classification.consequences_if_ignored,
                datetime.now()
            )
            
            print(f"  ✅ Aktion: {classification.primary_action.action_type.value}")
            print(f"  📊 Impact: {classification.impact_score}/10")
            print(f"  🎯 Button: {classification.primary_action.button_text}\n")
            
        except Exception as e:
            print(f"  ❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    await conn.close()
    print("\n✅ Klassifizierung abgeschlossen!")

if __name__ == '__main__':
    asyncio.run(classify_new_updates())
