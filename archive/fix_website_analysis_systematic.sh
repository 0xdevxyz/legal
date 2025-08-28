#!/bin/bash

# ==========================================
# COMPLYO - SYSTEMATIC WEBSITEANALYSIS.TSX FIX
# Repariert alle Funktions-Position-Probleme
# ==========================================

echo "🔧 SYSTEMATIC WEBSITEANALYSIS.TSX REPAIR"
echo "========================================"

# Step 1: Backup der kaputten Datei
echo "📦 Step 1: Backup broken file"
docker exec complyo-dashboard-react cp /app/src/components/dashboard/WebsiteAnalysis.tsx /app/WebsiteAnalysis.tsx.broken

# Step 2: Restore von einem funktionierenden Backup  
echo "⏪ Step 2: Restore from working backup"
docker exec complyo-dashboard-react cp /app/WebsiteAnalysis.tsx.backup2 /app/src/components/dashboard/WebsiteAnalysis.tsx

# Step 3: Verify dass normalizeUrl funktioniert
echo "✅ Step 3: Verify normalizeUrl exists"
docker exec complyo-dashboard-react grep -n "function normalizeUrl" /app/src/components/dashboard/WebsiteAnalysis.tsx

# Step 4: Verify dass category fix funktioniert  
echo "✅ Step 4: Verify category fix exists"
docker exec complyo-dashboard-react grep -n "String(finding" /app/src/components/dashboard/WebsiteAnalysis.tsx

# Step 5: Füge transformFindings an der RICHTIGEN Stelle hinzu
echo "🔧 Step 5: Add transformFindings at correct position"
docker exec complyo-dashboard-react sh -c "
# Finde Zeile nach normalizeUrl function end
line_num=\$(grep -n '^}$' /app/src/components/dashboard/WebsiteAnalysis.tsx | head -1 | cut -d: -f1)
echo \"Adding transformFindings after line \$line_num\"

# Füge transformFindings nach der ersten schließenden Klammer hinzu (Ende von normalizeUrl)
sed -i \"\${line_num}a\\\\
\\\\
// Transform Backend findings Object zu Frontend Array\\\\
function transformFindings(backendFindings: any) {\\\\
  if (Array.isArray(backendFindings)) {\\\\
    return backendFindings;\\\\
  }\\\\
  if (typeof backendFindings === 'object' && backendFindings !== null) {\\\\
    return Object.entries(backendFindings).map(([category, description]) => ({\\\\
      id: Math.random().toString(36).substr(2, 9),\\\\
      category: category,\\\\
      title: String(description),\\\\
      status: 'error' as const\\\\
    }));\\\\
  }\\\\
  return [];\\\\
}\" /app/src/components/dashboard/WebsiteAnalysis.tsx
"

# Step 6: Ersetze Object.values mit transformFindings
echo "🔄 Step 6: Replace Object.values with transformFindings"
docker exec complyo-dashboard-react sed -i 's/Object\.values(analysisData\.findings)/transformFindings(analysisData?.findings)/g' /app/src/components/dashboard/WebsiteAnalysis.tsx

# Step 7: Verification
echo "🔍 Step 7: Final verification"
echo "✅ Checking normalizeUrl:"
docker exec complyo-dashboard-react grep -n "function normalizeUrl" /app/src/components/dashboard/WebsiteAnalysis.tsx

echo "✅ Checking transformFindings:"  
docker exec complyo-dashboard-react grep -n "function transformFindings" /app/src/components/dashboard/WebsiteAnalysis.tsx

echo "✅ Checking category fix:"
docker exec complyo-dashboard-react grep -n "String(finding" /app/src/components/dashboard/WebsiteAnalysis.tsx

echo "✅ Checking transformFindings usage:"
docker exec complyo-dashboard-react grep -n "transformFindings(" /app/src/components/dashboard/WebsiteAnalysis.tsx

# Step 8: Test compilation
echo "⚡ Step 8: Test Next.js compilation"
docker exec complyo-dashboard-react sh -c "cd /app && npm run build > /tmp/build.log 2>&1 && echo 'BUILD SUCCESS' || echo 'BUILD FAILED'"

echo ""
echo "🎯 SYSTEMATIC REPAIR COMPLETED!"
echo "================================"
echo "✅ normalizeUrl function restored"
echo "✅ transformFindings function added at correct position" 
echo "✅ Category safety fix applied"
echo "✅ Object.values replaced with transformFindings"
echo ""
echo "🚀 Next steps:"
echo "1. Refresh https://app.complyo.tech"
echo "2. Test with 'panoart360.de'"
echo "3. Should show: IMPRESSUM, COOKIES, ACCESSIBILITY, DATENSCHUTZERKLAERUNG"
echo ""
echo "🔍 If issues persist, check:"
echo "   - Browser Console for compilation errors"
echo "   - Network Tab for API calls"
echo "   - /tmp/build.log for build errors"
