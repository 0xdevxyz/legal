#!/bin/bash

# ============================================================================
# RATING-VOLATILITY FIX - DEPLOYMENT SCRIPT
# ============================================================================

set -e  # Exit on error

cd /home/clawd/saas/legal

echo "🚀 Rating-Volatility Fix Deployment"
echo "===================================="
echo ""

# Step 1: Git Status
echo "1️⃣  Git Status..."
git status --short || echo "Git check skipped"
echo ""

# Step 2: Verify Code Files
echo "2️⃣  Verify Backend Files..."
ls -lh backend/compliance_engine/score_calculator.py || echo "❌ score_calculator.py nicht gefunden!"
grep -q "from compliance_engine.score_calculator import ScoreCalculator" backend/compliance_engine/scanner.py && echo "✅ scanner.py import OK" || echo "❌ scanner.py import fehlt!"
grep -q "from compliance_engine.score_calculator import ScoreCalculator" backend/compliance_engine/engine.py && echo "✅ engine.py import OK" || echo "❌ engine.py import fehlt!"
grep -q "from compliance_engine.score_calculator import ScoreCalculator" backend/main_production.py && echo "✅ main_production.py import OK" || echo "❌ main_production.py import fehlt!"
echo ""

# Step 3: Docker Compose Build
echo "3️⃣  Building Docker Image (docker compose build backend)..."
docker compose build backend
echo "✅ Build complete"
echo ""

# Step 4: Stop old containers
echo "4️⃣  Stopping old backend container..."
docker compose down backend 2>/dev/null || echo "No running backend to stop"
echo ""

# Step 5: Start new backend
echo "5️⃣  Starting new backend container (docker compose up -d backend)..."
docker compose up -d backend
sleep 3
echo "✅ Backend started"
echo ""

# Step 6: Verify Container
echo "6️⃣  Verify Backend Container..."
docker ps | grep complyo-backend && echo "✅ Container running" || echo "❌ Container not running!"
echo ""

# Step 7: Verify Import
echo "7️⃣  Verify ScoreCalculator Import in Container..."
docker exec complyo-backend python3 -c "from compliance_engine.score_calculator import ScoreCalculator; print('✅ ScoreCalculator Import OK')" && echo "✅ Import successful" || echo "❌ Import failed!"
echo ""

# Step 8: Check Logs
echo "8️⃣  Backend Logs (last 20 lines)..."
docker logs complyo-backend | tail -20
echo ""

# Step 9: Health Check
echo "9️⃣  Health Check..."
sleep 2
curl -s http://localhost:8002/health | jq '.' && echo "✅ Backend is healthy" || echo "⚠️  Health check failed"
echo ""

echo "🎉 Deployment Complete!"
echo ""
echo "Next Steps:"
echo "1. Test the API:"
echo "   curl -X POST http://localhost:8002/api/v2/analyze/complete \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"url\": \"https://compyo.de\"}'"
echo ""
echo "2. Run 3x to verify consistent score"
echo ""

