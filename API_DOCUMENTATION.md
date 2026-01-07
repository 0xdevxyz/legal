# Complyo API Documentation
## RESTful API v2 – Complete Reference

**Base URL:** `https://api.complyo.tech/api/v2`  
**Authentication:** Bearer Token (JWT)  
**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Scan API](#scan-api)
3. [Fix Generation API](#fix-generation-api)
4. [Fix Application API](#fix-application-api)
5. [Audit Log API](#audit-log-api)
6. [eRecht24 Integration](#erecht24-integration)
7. [Widget API](#widget-api)
8. [Legal News API](#legal-news-api)
9. [Rate Limiting](#rate-limiting)
10. [Error Handling](#error-handling)

---

## Authentication

### Get Access Token

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600,
  "user": {
    "user_id": 123,
    "email": "user@example.com",
    "plan": "expert"
  }
}
```

### Use Token

Include in Authorization header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## Scan API

### Scan Website

```http
POST /scan
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://example.com",
  "deep_scan": true,
  "include_screenshots": true
}
```

**Response:**
```json
{
  "scan_id": "scan_abc123",
  "url": "https://example.com",
  "status": "scanning",
  "estimated_time_seconds": 30,
  "created_at": "2025-11-23T10:30:00Z"
}
```

### Get Scan Results

```http
GET /scan/{scan_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "scan_id": "scan_abc123",
  "url": "https://example.com",
  "status": "completed",
  "compliance_score": 73,
  "violations": [
    {
      "id": "alt-text-missing-001",
      "category": "accessibility",
      "severity": "high",
      "title": "Fehlende Alt-Texte",
      "description": "15 Bilder ohne Alt-Text gefunden",
      "selector": "img[alt='']",
      "wcag_criteria": "1.1.1"
    }
  ],
  "widget_detected": {
    "has_accessibility_widget": true,
    "widget_type": "complyo-v5"
  },
  "scanned_at": "2025-11-23T10:30:45Z"
}
```

---

## Fix Generation API

### Generate Fix

```http
POST /fixes/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "issue_id": "alt-text-missing-001",
  "issue_category": "accessibility"
}
```

**Response:**
```json
{
  "fix_id": "fix_xyz789",
  "fix_type": "code",
  "title": "Alt-Text-Fix für Bilder",
  "description": "KI-generierte Alt-Texte für 15 Bilder",
  "code": "<img src=\"logo.png\" alt=\"Firmenlogo von Beispiel GmbH\">",
  "language": "html",
  "before_code": "<img src=\"logo.png\" alt=\"\">",
  "after_code": "<img src=\"logo.png\" alt=\"Firmenlogo von Beispiel GmbH\">",
  "estimated_time": "5 Minuten",
  "integration": {
    "where": "In Ihren HTML-Dateien",
    "instructions": "Ersetzen Sie die img-Tags mit den unten stehenden Versionen."
  },
  "metadata": {
    "transparency_note": "Generiert mit GPT-4",
    "confidence": 0.95
  },
  "generated_at": "2025-11-23T10:31:00Z"
}
```

### Export Fix

```http
POST /fixes/export
Authorization: Bearer {token}
Content-Type: application/json

{
  "fix_id": "fix_xyz789",
  "export_format": "zip"
}
```

**Response:** ZIP-Download or JSON with download_url

---

## Fix Application API

### Apply Fix

```http
POST /fixes/apply
Authorization: Bearer {token}
Content-Type: application/json

{
  "fix_id": "fix_xyz789",
  "deployment_method": "ftp",
  "credentials": {
    "host": "ftp.example.com",
    "port": "21",
    "username": "ftpuser",
    "password": "***",
    "path": "/public_html"
  },
  "backup_before_deploy": true,
  "user_confirmed": true,
  "fix_category": "accessibility",
  "fix_type": "code"
}
```

**Response:**
```json
{
  "success": true,
  "audit_id": "audit_abc123",
  "deployment_id": "deploy_def456",
  "deployment_method": "ftp",
  "files_deployed": [
    "/public_html/index.html",
    "/public_html/about.html"
  ],
  "backup_created": true,
  "backup_id": "backup_ghi789",
  "deployed_at": "2025-11-23T10:32:00Z",
  "rollback_available": true,
  "message": "Fix erfolgreich angewendet! Backup erstellt: backup_ghi789"
}
```

### Rollback Fix

```http
POST /fixes/rollback
Authorization: Bearer {token}
Content-Type: application/json

{
  "backup_id": "backup_ghi789",
  "deployment_method": "ftp",
  "credentials": {
    "host": "ftp.example.com",
    "port": "21",
    "username": "ftpuser",
    "password": "***",
    "path": "/public_html"
  }
}
```

**Response:**
```json
{
  "success": true,
  "audit_id": "audit_jkl012",
  "backup_id": "backup_ghi789",
  "message": "Rollback erfolgreich durchgeführt!"
}
```

### Preview on Staging (Premium)

```http
POST /fixes/apply/preview
Authorization: Bearer {token}
Content-Type: application/json

{
  "fix_id": "fix_xyz789",
  "create_screenshots": true
}
```

**Response:**
```json
{
  "success": true,
  "staging_url": "https://preview-xyz789.complyo.tech",
  "screenshot_before": "https://cdn.complyo.tech/screenshots/before_xyz.png",
  "screenshot_after": "https://cdn.complyo.tech/screenshots/after_xyz.png",
  "screenshot_diff": "https://cdn.complyo.tech/screenshots/diff_xyz.png",
  "status": "deployed",
  "message": "Staging-Environment bereit für Review"
}
```

### Get Apply Status

```http
GET /fixes/apply/status/{apply_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "apply_id": "deploy_def456",
  "status": "deployed",
  "progress": 100,
  "current_step": "completed",
  "error": null
}
```

---

## Audit Log API

### Get Audit Log

```http
GET /audit/log?limit=50&offset=0&action_type=applied
Authorization: Bearer {token}
```

**Response:**
```json
{
  "audit_log": [
    {
      "id": "audit_abc123",
      "fix_id": "fix_xyz789",
      "fix_category": "accessibility",
      "action_type": "applied",
      "deployment_method": "ftp",
      "applied_at": "2025-11-23T10:32:00Z",
      "success": true,
      "backup_id": "backup_ghi789",
      "rollback_available": true,
      "user_confirmed": true
    }
  ],
  "statistics": {
    "total_actions": 15,
    "fixes_applied": 8,
    "fixes_downloaded": 5,
    "rollbacks": 2,
    "success_rate": 93.3
  }
}
```

### Get Audit Statistics

```http
GET /audit/statistics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_actions": 15,
  "fixes_generated": 12,
  "fixes_downloaded": 5,
  "fixes_applied": 8,
  "rollbacks": 2,
  "successful_actions": 14,
  "failed_actions": 1,
  "success_rate": 93.3,
  "last_action_at": "2025-11-23T10:32:00Z",
  "total_backups": 8,
  "total_backup_size_mb": 15.4,
  "restored_backups": 2
}
```

---

## eRecht24 Integration

### Connect eRecht24 Account

```http
POST /erecht24/connect
Authorization: Bearer {token}
Content-Type: application/json

{
  "api_key": "your-erecht24-api-key",
  "project_key": "your-project-key"
}
```

### Get Legal Texts

```http
GET /erecht24/texts/{text_type}
Authorization: Bearer {token}
```

**text_type:** `impressum`, `privacy_policy`, `privacy_policy_social_media`

**Response:**
```json
{
  "text_type": "impressum",
  "html_content": "<h1>Impressum</h1><p>...</p>",
  "last_updated": "2025-11-20T14:30:00Z",
  "is_protected": true
}
```

---

## Widget API

### Get Widget Code

```http
GET /widgets/code/{site_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "widget_code": "<script src=\"https://cdn.complyo.tech/widget-v5.js\" data-site=\"abc123\"></script>",
  "site_id": "abc123",
  "version": "v5",
  "features": ["alt-text", "contrast", "font-size", "screen-reader"]
}
```

### Track Widget Event

```http
POST /widgets/track
Content-Type: application/json

{
  "site_id": "abc123",
  "event_type": "feature_used",
  "feature": "contrast_toggle",
  "session_id": "session_xyz"
}
```

---

## Legal News API

### Get Legal Updates

```http
GET /legal-news?limit=10&category=dsgvo
Authorization: Bearer {token}
```

**Response:**
```json
{
  "updates": [
    {
      "id": "update_001",
      "title": "Neue DSGVO-Richtlinie für Cookie-Banner",
      "summary": "Ab 2026 gelten strengere Regeln...",
      "relevance_score": 9,
      "urgency": "high",
      "affected_industries": ["e-commerce", "marketing"],
      "published_at": "2025-11-20T09:00:00Z",
      "source": "Bundesgesetzblatt"
    }
  ]
}
```

---

## Rate Limiting

### Limits by Plan

| Plan | Fix Generations | API Requests | Webhook Calls |
|------|----------------|--------------|---------------|
| AI | 10/hour | 100/day | 1000/day |
| Expert | Unlimited | 1000/day | 5000/day |
| Managed | Unlimited | Unlimited | Unlimited |

### Rate Limit Headers

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1700744400
```

### Rate Limit Exceeded

```json
{
  "error": "rate_limit_exceeded",
  "message": "Sie haben das Limit von 10 Fix-Generierungen pro Stunde erreicht.",
  "retry_after": 1800
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "invalid_input",
  "message": "issue_id ist erforderlich und darf nicht leer sein.",
  "details": {
    "field": "issue_id",
    "received": ""
  },
  "timestamp": "2025-11-23T10:35:00Z"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden (Premium feature or rate limit) |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Common Errors

**401 Unauthorized:**
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

**403 Forbidden (Premium):**
```json
{
  "error": "premium_required",
  "message": "SFTP/SSH-Deployment ist nur im Managed-Plan (3.000€/Mo) verfügbar."
}
```

**404 Not Found:**
```json
{
  "error": "not_found",
  "message": "Fix fix_xyz789 nicht gefunden oder nicht für diesen User verfügbar."
}
```

---

## Webhooks

### eRecht24 Webhook

**URL:** `POST /api/webhook/erecht24`

**Payload:**
```json
{
  "project_key": "your-project-key",
  "text_type": "impressum",
  "updated_at": "2025-11-23T10:00:00Z",
  "event": "text_updated"
}
```

### GitHub Webhook

**URL:** `POST /api/webhook/github`

**Payload:**
```json
{
  "action": "pull_request",
  "pr_merged": true,
  "fix_id": "fix_xyz789",
  "deployment_id": "deploy_def456",
  "repository": "username/repo-name"
}
```

---

## SDK Support

### JavaScript/TypeScript

```typescript
import { ComplyoClient } from '@complyo/sdk';

const client = new ComplyoClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.complyo.tech/api/v2'
});

// Scan Website
const scan = await client.scan({
  url: 'https://example.com'
});

// Generate Fix
const fix = await client.generateFix({
  issueId: scan.violations[0].id,
  issueCategory: 'accessibility'
});

// Apply Fix
const result = await client.applyFix({
  fixId: fix.fix_id,
  method: 'ftp',
  credentials: {...}
});
```

### Python

```python
from complyo import ComplyoClient

client = ComplyoClient(api_key='your-api-key')

# Scan Website
scan = client.scan(url='https://example.com')

# Generate Fix
fix = client.generate_fix(
    issue_id=scan['violations'][0]['id'],
    issue_category='accessibility'
)

# Apply Fix
result = client.apply_fix(
    fix_id=fix['fix_id'],
    method='ftp',
    credentials={...}
)
```

---

## Support

**Documentation:** https://docs.complyo.tech  
**API Status:** https://status.complyo.tech  
**Support Email:** api-support@complyo.tech  
**Discord:** https://discord.gg/complyo

---

**© 2025 Complyo.tech** – Compliance made easy

