# Complyo Production Deployment Guide

**Version:** 2.0  
**Date:** 2025-08-27  
**Status:** Production Ready  

---

## 🚀 Quick Production Deployment

### Prerequisites

- Ubuntu 20.04+ server with minimum 4GB RAM, 2 CPU cores, 50GB disk
- Docker & Docker Compose installed
- Root access for SSL certificate setup
- Domain DNS pointed to server IP

### 1-Command Production Deployment

```bash
sudo /opt/projects/saas-project-2/scripts/deploy-production.sh
```

This script will:
- ✅ Validate prerequisites
- ✅ Generate SSL certificates
- ✅ Build production images
- ✅ Deploy all services
- ✅ Setup monitoring
- ✅ Validate deployment

---

## 📋 Production Readiness Checklist

### ✅ CRITICAL SECURITY FIXES COMPLETED

| Component | Status | Description |
|-----------|--------|-------------|
| **SSL/HTTPS** | ✅ **FIXED** | Let's Encrypt certificates with auto-renewal |
| **Gateway Configuration** | ✅ **FIXED** | Production Nginx with security headers & rate limiting |
| **Environment Configuration** | ✅ **FIXED** | Production environment variables & secrets |
| **Rate Limiting** | ✅ **IMPLEMENTED** | Redis-based rate limiting on all endpoints |
| **Security Headers** | ✅ **IMPLEMENTED** | Complete security header configuration |
| **CORS Policy** | ✅ **IMPLEMENTED** | Strict CORS policy for production domains |
| **Authentication** | ✅ **ENHANCED** | JWT-based auth with proper middleware |
| **Input Validation** | ✅ **IMPLEMENTED** | Comprehensive input validation & sanitization |

### 🔒 SECURITY HARDENING

| Security Measure | Status | Implementation |
|------------------|--------|----------------|
| **Container Security** | ✅ | Non-root users, read-only containers where possible |
| **Network Security** | ✅ | Internal network isolation, localhost binding |
| **Secret Management** | ✅ | Strong passwords, environment variable isolation |
| **Database Security** | ✅ | Connection encryption, user permissions |
| **Logging & Monitoring** | ✅ | Comprehensive logging with Prometheus/Grafana |
| **Backup System** | ✅ | Automated backups with integrity verification |

### 📊 MONITORING & OBSERVABILITY

| Component | Status | Access URL |
|-----------|--------|------------|
| **Prometheus** | ✅ | http://localhost:9090 |
| **Grafana** | ✅ | http://localhost:3001 |
| **Loki (Logs)** | ✅ | http://localhost:3100 |
| **Alertmanager** | ✅ | http://localhost:9093 |

---

## 🏗️ Architecture Overview

### Production Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERNET                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              NGINX GATEWAY (SSL/Security)                  │
│  • SSL Termination   • Rate Limiting   • Security Headers │
└─────┬─────────────────────────────────────────────┬───────┘
      │                                             │
┌─────▼─────┐  ┌──────────────────┐  ┌──────────────▼───────┐
│ Frontend  │  │   Backend API    │  │   Monitoring Stack   │
│ Services  │  │                  │  │                      │
│           │  │ • Rate Limited   │  │ • Prometheus         │
│ • Landing │  │ • Cached         │  │ • Grafana            │
│ • Dashboard│  │ • Secured       │  │ • Loki               │
└─────┬─────┘  └─────────┬────────┘  └──────────────────────┘
      │                  │
      └──────┬───────────┘
             │
    ┌────────▼────────┐
    │  Data Services  │
    │                 │
    │ • PostgreSQL    │
    │ • Redis Cache   │
    │ • Backups       │
    └─────────────────┘
```

### Network Security

- **Internal Networks**: Services communicate via Docker networks
- **External Access**: Only necessary ports exposed to localhost
- **SSL Termination**: All external traffic encrypted
- **Rate Limiting**: Per-IP and per-endpoint limits

---

## 🔧 Manual Deployment Steps

If you prefer manual deployment or need to understand each step:

### Step 1: Environment Setup

```bash
# Navigate to project directory
cd /opt/projects/saas-project-2

# Copy and customize environment file
cp .env.production .env.production.local
# Edit passwords and API keys as needed
nano .env.production.local
```

### Step 2: SSL Certificate Setup

```bash
# Generate SSL certificates
sudo ./scripts/ssl-setup.sh setup

# Verify certificate status
sudo ./scripts/ssl-setup.sh status
```

### Step 3: Build Production Images

```bash
# Build all production images
docker-compose -f docker-compose.production.yml build --no-cache
```

### Step 4: Database Initialization

```bash
# Start database services
docker-compose -f docker-compose.production.yml up -d shared-postgres shared-redis

# Apply database optimizations
docker exec -i shared-postgres-production psql -U complyo_user -d complyo_db < backend/database_optimization.sql
```

### Step 5: Deploy Application Services

```bash
# Deploy backend
docker-compose -f docker-compose.production.yml up -d complyo-backend-direct

# Deploy frontend services  
docker-compose -f docker-compose.production.yml up -d complyo-dashboard complyo-landing

# Deploy gateway
docker-compose -f docker-compose.production.yml up -d complyo-gateway
```

### Step 6: Setup Monitoring

```bash
# Deploy monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d
```

### Step 7: Validation

```bash
# Test all endpoints
curl -k https://complyo.tech
curl -k https://app.complyo.tech  
curl -k https://api.complyo.tech/health

# Check service status
docker-compose -f docker-compose.production.yml ps
```

---

## 🔍 Post-Deployment Validation

### Service Health Checks

```bash
# Check all container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test API endpoints
curl -s https://api.complyo.tech/health | jq
curl -s https://api.complyo.tech/ | jq

# Test rate limiting
for i in {1..15}; do curl -s https://api.complyo.tech/health; done
```

### SSL Certificate Validation

```bash
# Check certificate expiry
openssl s_client -connect complyo.tech:443 -servername complyo.tech 2>/dev/null | \
  openssl x509 -noout -dates

# Test SSL security rating
curl -s "https://api.ssllabs.com/api/v3/analyze?host=complyo.tech"
```

### Performance Testing

```bash
# Basic load test
ab -n 100 -c 10 https://api.complyo.tech/health

# Monitor resource usage
docker stats
```

---

## 🔧 Maintenance Operations

### Backup Management

```bash
# Create full backup
./scripts/backup-system.sh backup full

# List available backups  
./scripts/backup-system.sh list

# Verify backup integrity
./scripts/backup-system.sh verify /path/to/backup.sql.gz
```

### SSL Certificate Renewal

```bash
# Manual renewal (automatic via cron)
sudo ./scripts/ssl-setup.sh renew

# Test renewal process
sudo certbot renew --dry-run
```

### Log Management

```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f complyo-backend-direct

# View nginx logs
docker-compose -f docker-compose.production.yml logs -f complyo-gateway

# View system logs
tail -f /var/log/nginx/access.log
```

### Performance Monitoring

```bash
# Database performance
docker exec shared-postgres-production psql -U complyo_user -d complyo_db -c "\
  SELECT query, calls, total_time, total_time/calls as avg_time \
  FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Redis performance  
docker exec shared-redis-production redis-cli info stats
```

---

## 🚨 Emergency Procedures

### Rollback Procedure

```bash
# Stop current deployment
docker-compose -f docker-compose.production.yml down

# Restore from backup
./scripts/backup-system.sh restore /path/to/backup.sql.gz --confirm

# Deploy previous version
git checkout previous-tag
./scripts/deploy-production.sh
```

### Security Incident Response

1. **Immediate Actions**:
   ```bash
   # Block suspicious IPs
   iptables -A INPUT -s SUSPICIOUS_IP -j DROP
   
   # Review access logs
   grep "SUSPICIOUS_PATTERN" /var/log/nginx/access.log
   ```

2. **Investigation**:
   ```bash
   # Check audit logs
   docker exec shared-postgres-production psql -U complyo_user -d complyo_db -c \
     "SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours' ORDER BY created_at DESC;"
   ```

3. **Recovery**:
   - Change all passwords
   - Revoke compromised API keys
   - Force user re-authentication

### Database Recovery

```bash
# Emergency database backup
./scripts/backup-system.sh backup full

# Point-in-time recovery (if WAL archiving enabled)
# [Detailed recovery procedures would go here]
```

---

## 📊 Monitoring Dashboards

### Key Metrics to Monitor

| Metric | Critical Threshold | Warning Threshold |
|--------|-------------------|-------------------|
| **API Response Time** | > 2s | > 1s |
| **Error Rate** | > 5% | > 1% |
| **CPU Usage** | > 85% | > 70% |
| **Memory Usage** | > 90% | > 80% |
| **Disk Usage** | > 95% | > 85% |
| **SSL Certificate Expiry** | < 7 days | < 30 days |

### Grafana Dashboard URLs

- **System Overview**: http://localhost:3001/d/system-overview
- **Application Metrics**: http://localhost:3001/d/app-metrics  
- **Security Dashboard**: http://localhost:3001/d/security-metrics

### Alert Configurations

Alerts are configured for:
- Service downtime (> 1 minute)
- High error rates (> 5% for 2 minutes)
- Resource exhaustion (CPU/Memory > 90% for 5 minutes)
- SSL certificate expiry (< 7 days)
- Backup failures

---

## 🔐 Security Compliance

### Data Protection (GDPR)

- **Data Retention**: 730 days (configurable)
- **Right to be Forgotten**: Implemented via `gdpr_delete_user_data()` function
- **Data Export**: Available via API endpoints
- **Audit Logging**: Complete audit trail of all data operations

### Security Standards

- **TLS 1.2/1.3**: Only modern TLS versions accepted
- **HSTS**: HTTP Strict Transport Security enabled
- **CSP**: Content Security Policy configured
- **Rate Limiting**: 10 requests/second general, 3/second for analysis
- **Input Validation**: All inputs validated and sanitized

### Compliance Reporting

```bash
# Generate security report
./scripts/security-audit.sh report

# Check GDPR compliance
./scripts/gdpr-compliance-check.sh
```

---

## 🎯 Production Performance Targets

### Service Level Objectives (SLOs)

| Service | Availability | Response Time | Error Rate |
|---------|--------------|---------------|------------|
| **API** | 99.9% | < 500ms | < 0.1% |
| **Frontend** | 99.9% | < 2s | < 0.1% |
| **Database** | 99.95% | < 100ms | < 0.01% |

### Capacity Planning

| Resource | Current | Target | Scale Trigger |
|----------|---------|---------|---------------|
| **Concurrent Users** | 100 | 1000 | > 80% capacity |
| **API Requests/sec** | 100 | 1000 | > 70% capacity |
| **Database Connections** | 50 | 100 | > 80% usage |

---

## 📞 Support & Contact

### Production Support

- **Primary Contact**: DevOps Team <devops@complyo.tech>
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **Status Page**: https://status.complyo.tech

### Documentation

- **API Documentation**: https://api.complyo.tech/docs (development only)
- **System Architecture**: [Internal Wiki]
- **Runbooks**: `/opt/projects/saas-project-2/docs/runbooks/`

### Change Management

All production changes must:
1. Pass automated testing
2. Be reviewed by security team
3. Include rollback procedures
4. Be deployed during maintenance windows

---

## ✅ Deployment Verification

After completing the deployment, verify these items:

### Functional Tests
- [ ] Landing page loads correctly
- [ ] Dashboard application works
- [ ] API endpoints respond correctly
- [ ] SSL certificates are valid
- [ ] Monitoring dashboards accessible

### Security Tests  
- [ ] Rate limiting works
- [ ] CORS policy enforced
- [ ] Security headers present
- [ ] No debug information exposed
- [ ] Authentication required where appropriate

### Performance Tests
- [ ] Response times within SLO
- [ ] Database queries optimized
- [ ] Caching working correctly
- [ ] Resource usage within limits

### Operational Tests
- [ ] Backups running automatically
- [ ] Log aggregation working
- [ ] Alerts configured and tested
- [ ] SSL auto-renewal scheduled
- [ ] Monitoring data flowing

---

**🎉 Congratulations! Complyo is now production-ready with enterprise-grade security, monitoring, and reliability.**

For questions or issues, refer to the troubleshooting guide or contact the DevOps team.