# 🗄️ Database Migrations mit Alembic

> Complyo verwendet Alembic für versionierte Datenbankmigrationen.

---

## 📋 Quick Reference

```bash
cd backend

# Alle Migrationen anwenden
python migrate.py upgrade

# Eine Migration zurückrollen
python migrate.py downgrade

# Aktuelle Version anzeigen
python migrate.py current

# Migrationshistorie anzeigen
python migrate.py history

# Neue Migration erstellen
python migrate.py new "add user preferences table"

# Bestehende DB als aktuell markieren (Erstsetup)
python migrate.py stamp head
```

---

## 🚀 Ersteinrichtung

### Für neue Datenbanken

```bash
# 1. Umgebungsvariable setzen
export DATABASE_URL=postgresql://user:pass@localhost:5432/complyo_db

# 2. Alle Migrationen anwenden
python migrate.py upgrade
```

### Für bestehende Datenbanken

Wenn die Datenbank bereits existiert (z.B. aus `database_setup.sql`):

```bash
# 1. DB als "bereits migriert" markieren
python migrate.py stamp head

# 2. Ab jetzt normale Migrationen verwenden
python migrate.py upgrade
```

---

## 📝 Neue Migration erstellen

### Manuell (empfohlen)

```bash
# 1. Migration erstellen
python migrate.py new "add user preferences table"

# 2. Generierte Datei bearbeiten
# alembic/versions/YYYYMMDD_HHMM_xxxx_add_user_preferences_table.py
```

### Beispiel-Migration

```python
"""add user preferences table

Revision ID: abc123
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'abc123'
down_revision = '0001'

def upgrade() -> None:
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('theme', sa.String(50), server_default='light'),
        sa.Column('language', sa.String(10), server_default='de'),
        sa.Column('email_notifications', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'])

def downgrade() -> None:
    op.drop_table('user_preferences')
```

---

## 🔄 Workflow

### Entwicklung

```bash
# 1. Feature-Branch erstellen
git checkout -b feature/user-preferences

# 2. Migration erstellen
python migrate.py new "add user preferences"

# 3. Migration bearbeiten
code alembic/versions/...

# 4. Lokal testen
python migrate.py upgrade

# 5. Committen
git add alembic/
git commit -m "feat: add user preferences migration"
```

### Deployment

```bash
# In CI/CD oder auf dem Server:
python migrate.py upgrade

# Bei Problemen:
python migrate.py downgrade
```

---

## ⚠️ Best Practices

### ✅ DO

- Immer `downgrade()` implementieren
- Kleine, fokussierte Migrationen
- Migrationen vor dem Merge testen
- Indizes für häufig abgefragte Spalten erstellen
- Foreign Keys mit `ON DELETE` definieren

### ❌ DON'T

- Daten in Migrationen löschen ohne Backup
- Spalten umbenennen (lieber: neue Spalte + Daten kopieren + alte löschen)
- Große Datenmengen in einer Transaktion ändern
- Migrationen nach dem Merge ändern

---

## 🛠️ Troubleshooting

### "Target database is not up to date"

```bash
# Aktuelle Version prüfen
python migrate.py current

# Fehlende Migrationen anwenden
python migrate.py upgrade
```

### "Can't locate revision"

```bash
# Revision-Historie prüfen
python migrate.py history

# Ggf. DB-Status zurücksetzen
python migrate.py stamp <last_known_revision>
```

### Migration fehlgeschlagen

```bash
# 1. Fehler analysieren
docker-compose logs backend

# 2. Manuell korrigieren (falls nötig)
psql -h localhost -U complyo_user -d complyo_db

# 3. Migration erneut versuchen
python migrate.py upgrade
```

---

## 📁 Dateistruktur

```
backend/
├── alembic.ini              # Alembic Konfiguration
├── migrate.py               # Helper-Skript
└── alembic/
    ├── env.py               # Alembic Environment
    ├── script.py.mako       # Migration Template
    └── versions/            # Migration Dateien
        └── 20251125_0001_initial_schema.py
```

---

## 🔗 Weitere Ressourcen

- [Alembic Dokumentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Migration Guide](https://docs.sqlalchemy.org/en/20/)


