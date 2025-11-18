# Integration Plan: Neue Gesetze → Bestehender Compliance-Workflow

## 🎯 Ziel
Automatische Integration erkannter Gesetzesänderungen in den bestehenden Compliance-Workflow, sodass Kunden nahtlos durch die Umsetzung geführt werden.

---

## 📊 Aktueller Status

### Bestehende Systeme:
1. **Legal Change Monitor** - Erkennt Gesetzesänderungen ✅
2. **Compliance Scanner** - Analysiert Websites ✅
3. **AI Fix Generator** - Generiert Fixes ✅
4. **Workflow Engine** - Führt User durch Optimierung ✅
5. **Cookie Compliance** - Verwaltet Cookie-Banner ✅

### Problem:
- Systeme arbeiten isoliert
- Keine automatische Verknüpfung zwischen erkannten Gesetzen und aktiven Scans
- Kein automatischer Workflow-Trigger bei neuen Gesetzen

---

## 🔄 Integration-Workflow

### Phase 1: Gesetz wird erkannt
```
Legal Change Monitor
    ↓
Neue Gesetzesänderung in DB
    ↓
Trigger: background_task
```

### Phase 2: Impact-Analyse & User-Matching
```
Für jeden aktiven User:
    ↓
Hole Website-Konfiguration
    ↓
Analysiere Impact (KI)
    ↓
Speichere in legal_change_impacts
    ↓
Wenn betroffen → Phase 3
```

### Phase 3: Workflow-Integration
```
Betroffener User
    ↓
Erstelle neue Compliance-Journey
    ↓
Füge spezifische Steps hinzu
    ↓
Sende Notification
    ↓
User startet Workflow
```

### Phase 4: Automatische Umsetzung
```
User im Workflow
    ↓
Step 1: Problem verstehen (AI-Erklärung)
    ↓
Step 2: Scan durchführen (automatisch)
    ↓
Step 3: Fix anwenden (semi-automatisch)
    ↓
Step 4: Validation (automatisch)
    ↓
Step 5: Dokumentation (automatisch)
    ↓
✅ Compliance erreicht
```

---

## 🛠️ Technische Implementierung

### 1. Workflow-Template für Gesetzesänderungen

**Datei:** `compliance_engine/legal_change_workflow.py`

```python
from compliance_engine.workflow_engine import WorkflowStep, UserSkillLevel
from legal_change_monitor import LegalChange, LegalArea
from typing import List, Dict, Any

class LegalChangeWorkflowGenerator:
    """
    Generiert automatisch Workflows für Gesetzesänderungen
    """
    
    def generate_workflow(
        self,
        legal_change: LegalChange,
        user_skill_level: UserSkillLevel,
        affected_components: List[str]
    ) -> List[WorkflowStep]:
        """
        Erstellt einen personalisierten Workflow für eine Gesetzesänderung
        """
        steps = []
        
        # Step 1: Einführung & Kontext
        steps.append(WorkflowStep(
            id=f"legal_intro_{legal_change.id}",
            title=f"Neue Gesetzesänderung: {legal_change.title}",
            description=self._generate_intro(legal_change, user_skill_level),
            action_type="information",
            estimated_duration=5,
            ai_assistance_level="high"
        ))
        
        # Step 2: Website-Analyse
        steps.append(WorkflowStep(
            id=f"legal_scan_{legal_change.id}",
            title="Compliance-Status prüfen",
            description="Automatische Analyse Ihrer Website",
            action_type="automated_scan",
            estimated_duration=2,
            ai_assistance_level="full"
        ))
        
        # Step 3: Bereich-spezifische Fixes
        for area in legal_change.affected_areas:
            area_steps = self._generate_area_steps(
                legal_change, 
                area, 
                user_skill_level
            )
            steps.extend(area_steps)
        
        # Step 4: Validierung
        steps.append(WorkflowStep(
            id=f"legal_validate_{legal_change.id}",
            title="Änderungen überprüfen",
            description="Automatische Validierung der Umsetzung",
            action_type="automated_validation",
            estimated_duration=3,
            ai_assistance_level="full"
        ))
        
        # Step 5: Dokumentation
        steps.append(WorkflowStep(
            id=f"legal_doc_{legal_change.id}",
            title="Compliance-Nachweis erstellen",
            description="Automatische Dokumentation für Audit",
            action_type="documentation",
            estimated_duration=2,
            ai_assistance_level="full"
        ))
        
        return steps
    
    def _generate_intro(
        self,
        legal_change: LegalChange,
        skill_level: UserSkillLevel
    ) -> str:
        """Generiert personalisierte Einführung"""
        if skill_level == UserSkillLevel.BEGINNER:
            return f"""
            ## Was bedeutet das für Sie?
            
            {legal_change.description}
            
            ### Warum ist das wichtig?
            - Inkrafttreten: {legal_change.effective_date.strftime('%d.%m.%Y')}
            - Dringlichkeit: {legal_change.severity.value.upper()}
            
            ### Was müssen Sie tun?
            Wir führen Sie Schritt für Schritt durch die notwendigen Änderungen.
            Die meisten Schritte laufen automatisch ab.
            """
        else:
            return f"""
            ## Gesetzesänderung Details
            
            **Quelle:** {legal_change.source}
            **Link:** {legal_change.source_url}
            
            ### Anforderungen:
            {chr(10).join([f"- {req}" for req in legal_change.requirements])}
            
            ### Betroffene Bereiche:
            {', '.join([area.value for area in legal_change.affected_areas])}
            """
    
    def _generate_area_steps(
        self,
        legal_change: LegalChange,
        area: LegalArea,
        skill_level: UserSkillLevel
    ) -> List[WorkflowStep]:
        """Generiert Steps für spezifischen Bereich"""
        steps = []
        
        if area == LegalArea.COOKIE_COMPLIANCE:
            steps.append(WorkflowStep(
                id=f"fix_cookies_{legal_change.id}",
                title="Cookie-Banner anpassen",
                description="Automatische Anpassung Ihres Cookie-Banners",
                action_type="automated_fix",
                target_component="cookie_banner",
                estimated_duration=5,
                ai_assistance_level="full" if skill_level == UserSkillLevel.BEGINNER else "medium"
            ))
        
        elif area == LegalArea.DATENSCHUTZ:
            steps.append(WorkflowStep(
                id=f"fix_privacy_{legal_change.id}",
                title="Datenschutzerklärung aktualisieren",
                description="Automatisches Update mit eRecht24",
                action_type="automated_fix",
                target_component="privacy_policy",
                estimated_duration=3,
                ai_assistance_level="full"
            ))
        
        elif area == LegalArea.IMPRESSUM:
            steps.append(WorkflowStep(
                id=f"fix_imprint_{legal_change.id}",
                title="Impressum prüfen",
                description="Überprüfung auf neue Anforderungen",
                action_type="validation",
                target_component="imprint",
                estimated_duration=5,
                ai_assistance_level="medium"
            ))
        
        elif area == LegalArea.BARRIEREFREIHEIT:
            steps.append(WorkflowStep(
                id=f"fix_accessibility_{legal_change.id}",
                title="Barrierefreiheit verbessern",
                description="Umsetzung neuer WCAG-Anforderungen",
                action_type="semi_automated_fix",
                target_component="accessibility",
                estimated_duration=15,
                ai_assistance_level="high"
            ))
        
        return steps
```

### 2. Automatische Workflow-Erstellung

**Datei:** `compliance_engine/workflow_integration_legal.py`

```python
from database_service import DatabaseService
from legal_change_monitor import legal_monitor, LegalChange
from compliance_engine.legal_change_workflow import LegalChangeWorkflowGenerator
from typing import List
import json

db_service = DatabaseService()
workflow_generator = LegalChangeWorkflowGenerator()

async def integrate_legal_change_into_workflows(legal_change: LegalChange):
    """
    Integriert eine neue Gesetzesänderung in User-Workflows
    """
    print(f"🔄 Integrating {legal_change.title} into workflows...")
    
    # 1. Finde alle betroffenen User
    async with db_service.pool.acquire() as conn:
        impacts = await conn.fetch("""
            SELECT user_id, affected_components, urgency
            FROM legal_change_impacts
            WHERE legal_change_id = $1 
            AND is_affected = true
            AND status != 'completed'
        """, legal_change.id)
    
    print(f"📊 Found {len(impacts)} affected users")
    
    # 2. Für jeden User: Workflow erstellen
    for impact in impacts:
        await create_user_workflow(
            legal_change=legal_change,
            user_id=impact['user_id'],
            affected_components=impact['affected_components'],
            urgency=impact['urgency']
        )
    
    print(f"✅ Workflows created for {len(impacts)} users")

async def create_user_workflow(
    legal_change: LegalChange,
    user_id: str,
    affected_components: List[str],
    urgency: str
):
    """
    Erstellt einen personalisierten Workflow für einen User
    """
    async with db_service.pool.acquire() as conn:
        # Hole User-Skill-Level
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        
        skill_level = UserSkillLevel.BEGINNER  # Default
        
        # Generiere Workflow-Steps
        steps = workflow_generator.generate_workflow(
            legal_change=legal_change,
            user_skill_level=skill_level,
            affected_components=affected_components
        )
        
        # Erstelle Journey
        journey_id = await conn.fetchval("""
            INSERT INTO compliance_journeys (
                user_id,
                title,
                description,
                status,
                priority,
                due_date,
                metadata
            ) VALUES ($1, $2, $3, 'active', $4, $5, $6)
            RETURNING id
        """,
            user_id,
            f"Gesetzesänderung: {legal_change.title}",
            f"Umsetzung erforderlich bis {legal_change.effective_date.strftime('%d.%m.%Y')}",
            1 if urgency == 'critical' else 2 if urgency == 'high' else 3,
            legal_change.effective_date,
            json.dumps({
                'legal_change_id': legal_change.id,
                'auto_generated': True,
                'source': 'legal_change_monitor'
            })
        )
        
        # Füge Steps hinzu
        for i, step in enumerate(steps):
            await conn.execute("""
                INSERT INTO workflow_steps (
                    journey_id,
                    step_order,
                    title,
                    description,
                    action_type,
                    target_component,
                    estimated_duration,
                    ai_assistance_level,
                    status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
            """,
                journey_id,
                i + 1,
                step.title,
                step.description,
                step.action_type,
                step.target_component,
                step.estimated_duration,
                step.ai_assistance_level
            )
        
        # Sende Notification
        await send_workflow_notification(user_id, legal_change, journey_id)
        
        print(f"✅ Workflow created for user {user_id}: Journey #{journey_id}")

async def send_workflow_notification(
    user_id: str,
    legal_change: LegalChange,
    journey_id: int
):
    """
    Sendet Notification an User über neuen Workflow
    """
    # TODO: Email-Service integration
    # TODO: In-App notification
    pass
```

### 3. Background Task Integration

**In:** `background_worker.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from legal_change_monitor import legal_monitor
from compliance_engine.workflow_integration_legal import integrate_legal_change_into_workflows

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2, minute=0)  # Täglich 2:00 Uhr
async def daily_legal_monitoring_and_integration():
    """
    Tägliche Überprüfung auf Gesetzesänderungen und Integration
    """
    if not legal_monitor:
        return
    
    # 1. Suche nach neuen Gesetzen
    changes = await legal_monitor.monitor_legal_changes()
    
    if not changes:
        print("ℹ️ No new legal changes detected")
        return
    
    print(f"🔍 Detected {len(changes)} new legal changes")
    
    # 2. Für jede Änderung
    for change in changes:
        # Speichere in DB (schon durch monitor_legal_changes)
        
        # 3. Führe Impact-Analyse für ALLE User durch
        await run_impact_analysis_for_all_users(change)
        
        # 4. Integriere in Workflows
        await integrate_legal_change_into_workflows(change)
    
    print(f"✅ Legal monitoring and integration completed")

async def run_impact_analysis_for_all_users(legal_change):
    """
    Führt Impact-Analyse für alle aktiven User durch
    """
    async with db_service.pool.acquire() as conn:
        users = await conn.fetch("""
            SELECT id, email FROM users 
            WHERE is_active = true 
            AND subscription_status = 'active'
        """)
    
    for user in users:
        # Trigger Impact-Analyse (background task)
        # ... (siehe _run_impact_analysis in legal_change_routes.py)
        pass
```

### 4. Integration mit bestehenden Scans

**Datei:** `compliance_engine/legal_scan_integration.py`

```python
async def enrich_scan_with_legal_changes(scan_result: Dict[str, Any], user_id: str):
    """
    Reichert Scan-Ergebnis mit relevanten Gesetzesänderungen an
    """
    async with db_service.pool.acquire() as conn:
        # Hole betroffene Gesetzesänderungen
        legal_impacts = await conn.fetch("""
            SELECT 
                lc.id,
                lc.title,
                lc.severity,
                lc.effective_date,
                lci.urgency,
                lci.affected_components
            FROM legal_change_impacts lci
            JOIN legal_changes lc ON lci.legal_change_id = lc.id
            WHERE lci.user_id = $1 
            AND lci.is_affected = true
            AND lci.status != 'completed'
            ORDER BY lc.severity DESC, lc.effective_date ASC
        """, user_id)
        
        if legal_impacts:
            scan_result['legal_updates'] = {
                'count': len(legal_impacts),
                'critical_count': sum(1 for li in legal_impacts if li['severity'] == 'critical'),
                'changes': [
                    {
                        'id': li['id'],
                        'title': li['title'],
                        'severity': li['severity'],
                        'urgency': li['urgency'],
                        'deadline': li['effective_date'].isoformat(),
                        'affected_components': list(li['affected_components'])
                    }
                    for li in legal_impacts
                ]
            }
    
    return scan_result
```

---

## 📅 Implementierungs-Roadmap

### Sprint 1: Workflow-Template (Woche 1)
- [ ] `legal_change_workflow.py` erstellen
- [ ] Area-spezifische Step-Generierung
- [ ] Testing mit verschiedenen Skill-Levels

### Sprint 2: Automatische Integration (Woche 2)
- [ ] `workflow_integration_legal.py` implementieren
- [ ] User-Workflow-Erstellung automatisieren
- [ ] Notification-System anbinden

### Sprint 3: Background Processing (Woche 3)
- [ ] Background Task für tägliches Monitoring
- [ ] Impact-Analyse für alle User
- [ ] Workflow-Trigger automatisieren

### Sprint 4: Scan-Integration (Woche 4)
- [ ] Scan-Ergebnisse mit Legal Changes anreichern
- [ ] Dashboard-Anzeige erweitern
- [ ] Testing & Refinement

---

## 🎯 Erfolgs-Metriken

1. **Automatisierungsgrad:** >80% der Schritte automatisch
2. **Time-to-Compliance:** <24h nach Gesetzesänderung
3. **User-Completion-Rate:** >90% schließen Workflow ab
4. **False-Positive-Rate:** <5% nicht-betroffene User

---

## 🔐 Sicherheit & Qualität

- **Validation:** Jeder automatische Fix wird vor Anwendung validiert
- **Rollback:** Automatisches Rollback bei Fehlern
- **Audit-Log:** Vollständige Nachvollziehbarkeit
- **Expert-Review:** Kritische Fixes erfordern manuelle Freigabe

---

## 📞 Support & Eskalation

### Level 1: Automatisch
- Standard-Fixes
- Bekannte Patterns
- Niedrige Komplexität

### Level 2: Semi-Automatisch
- User-Bestätigung erforderlich
- Mittlere Komplexität
- Manuelle Nachbearbeitung möglich

### Level 3: Manuell
- Expert-Review erforderlich
- Hohe Komplexität
- Individueller Support

---

## 🚀 Quick Start

1. **Implementiere Basis:**
   ```bash
   cd backend
   touch compliance_engine/legal_change_workflow.py
   touch compliance_engine/workflow_integration_legal.py
   ```

2. **Update Background Worker:**
   ```python
   # In background_worker.py
   scheduler.add_job(daily_legal_monitoring_and_integration, ...)
   ```

3. **Testing:**
   ```bash
   # Simuliere Gesetzesänderung
   curl -X POST http://localhost:8002/api/legal-changes/monitor/run
   ```

4. **Monitor:**
   ```bash
   # Prüfe Logs
   docker logs complyo-backend -f | grep "Legal"
   ```

---

## 📊 Dashboard-Ansicht

```
┌─────────────────────────────────────┐
│ ⚖️  Gesetzesänderungen             │
├─────────────────────────────────────┤
│                                     │
│  🔴 3 Kritische Änderungen          │
│  🟡 5 Ausstehende Workflows         │
│                                     │
│  Nächste Deadline:                  │
│  "Cookie-Banner Pflicht"            │
│  📅 01.01.2025 (21 Tage)           │
│                                     │
│  ┌─────────────────────────┐       │
│  │ Workflow starten  →     │       │
│  └─────────────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

