"""
Complyo Abmahn-Risiko-Kalkulator
Berechnet konkrete Abmahnrisiken in Euro basierend auf gefundenen Compliance-Verstößen
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class ViolationType(Enum):
    """Types of compliance violations with base risk values"""
    MISSING_IMPRESSUM = ("impressum_missing", 3000, "Fehlendes Impressum")
    INCOMPLETE_IMPRESSUM = ("impressum_incomplete", 1500, "Unvollständiges Impressum")
    MISSING_PRIVACY_POLICY = ("privacy_missing", 5000, "Fehlende Datenschutzerklärung")
    INCOMPLETE_PRIVACY_POLICY = ("privacy_incomplete", 2000, "Unvollständige Datenschutzerklärung")
    COOKIE_NO_CONSENT = ("cookie_no_consent", 4000, "Cookies ohne Einwilligung")
    TRACKING_WITHOUT_CONSENT = ("tracking_no_consent", 3000, "Tracking ohne Einwilligung")
    NO_SSL = ("ssl_missing", 2000, "Keine SSL-Verschlüsselung")
    ACCESSIBILITY_VIOLATIONS = ("accessibility_issues", 1000, "Barrierefreiheits-Verstöße")
    SOCIAL_MEDIA_NO_CONSENT = ("social_media_no_consent", 1500, "Social Media ohne Einwilligung")
    CONTACT_DATA_MISSING = ("contact_missing", 800, "Fehlende Kontaktdaten")

    def __init__(self, code: str, base_risk_euro: int, description: str):
        self.code = code
        self.base_risk_euro = base_risk_euro
        self.description = description

@dataclass
class RiskFactor:
    """Risk multiplication factor based on various criteria"""
    name: str
    multiplier: float
    description: str

@dataclass
class RiskAssessment:
    """Complete risk assessment result"""
    base_risk_euro: int
    adjusted_risk_euro: int
    risk_factors: List[RiskFactor]
    violation_details: List[Dict[str, Any]]
    total_violations: int
    risk_level: str  # "low", "medium", "high", "critical"
    recommendations: List[str]

class ComplianceRiskCalculator:
    """Calculate compliance risks and potential fining amounts"""
    
    def __init__(self):
        self.risk_factors = {
            "company_size": {
                "startup": 0.7,    # Smaller companies often get lower fines
                "small": 0.8,      # < 50 employees
                "medium": 1.0,     # 50-250 employees  
                "large": 1.3,      # > 250 employees
                "enterprise": 1.5  # > 1000 employees
            },
            "industry": {
                "general": 1.0,
                "ecommerce": 1.2,     # Higher risk due to data processing
                "healthcare": 1.4,    # Heavily regulated
                "finance": 1.5,       # Maximum regulatory scrutiny
                "legal": 1.3,         # Expected to know better
                "technology": 1.1     # Moderate increase
            },
            "data_sensitivity": {
                "basic": 1.0,         # Just contact forms
                "personal": 1.2,      # Personal data collection
                "sensitive": 1.5,     # Health, financial data
                "special": 1.8        # Biometric, genetic data
            },
            "revenue": {
                "micro": 0.6,         # < 100k revenue
                "small": 0.8,         # < 1M revenue
                "medium": 1.0,        # < 10M revenue
                "large": 1.3,         # < 100M revenue
                "enterprise": 1.6     # > 100M revenue
            }
        }
    
    def calculate_risk(self, 
                      violations: List[Dict[str, Any]], 
                      company_profile: Dict[str, str] = None) -> RiskAssessment:
        """
        Calculate comprehensive risk assessment
        
        Args:
            violations: List of compliance violations from scanner
            company_profile: Company information for risk adjustment
        """
        if not violations:
            return self._create_zero_risk_assessment()
        
        # Calculate base risk from violations
        base_risk = self._calculate_base_risk(violations)
        
        # Apply risk factors based on company profile
        risk_factors = self._calculate_risk_factors(company_profile or {})
        
        # Calculate adjusted risk
        total_multiplier = self._calculate_total_multiplier(risk_factors)
        adjusted_risk = int(base_risk * total_multiplier)
        
        # Determine risk level
        risk_level = self._determine_risk_level(adjusted_risk, len(violations))
        
        # Generate recommendations
        recommendations = self._generate_risk_recommendations(violations, risk_level)
        
        return RiskAssessment(
            base_risk_euro=base_risk,
            adjusted_risk_euro=adjusted_risk,
            risk_factors=risk_factors,
            violation_details=violations,
            total_violations=len(violations),
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _calculate_base_risk(self, violations: List[Dict[str, Any]]) -> int:
        """Calculate base risk from violations"""
        total_risk = 0
        
        for violation in violations:
            # Get risk amount from violation or use default mapping
            if 'risk_euro' in violation:
                total_risk += violation['risk_euro']
            else:
                # Fallback mapping based on category and severity
                risk = self._map_violation_to_risk(violation)
                total_risk += risk
        
        return total_risk
    
    def _map_violation_to_risk(self, violation: Dict[str, Any]) -> int:
        """Map violation to risk amount based on category and severity"""
        category = violation.get('category', '').lower()
        severity = violation.get('severity', 'warning')
        
        # Base risk mapping
        category_risks = {
            'impressum': 2500,
            'datenschutz': 4000,
            'cookie-compliance': 3500,
            'barrierefreiheit': 1000,
            'sicherheit': 2000,
            'social media': 1500
        }
        
        base_risk = category_risks.get(category, 1000)
        
        # Severity multipliers
        severity_multipliers = {
            'critical': 1.0,
            'warning': 0.6,
            'info': 0.2
        }
        
        return int(base_risk * severity_multipliers.get(severity, 0.6))
    
    def _calculate_risk_factors(self, company_profile: Dict[str, str]) -> List[RiskFactor]:
        """Calculate risk factors based on company profile"""
        factors = []
        
        # Company size factor
        company_size = company_profile.get('company_size', 'small')
        size_multiplier = self.risk_factors['company_size'].get(company_size, 1.0)
        if size_multiplier != 1.0:
            factors.append(RiskFactor(
                name=f"Unternehmensgröße: {company_size}",
                multiplier=size_multiplier,
                description=f"{'Erhöhtes' if size_multiplier > 1 else 'Reduziertes'} Risiko aufgrund der Unternehmensgröße"
            ))
        
        # Industry factor
        industry = company_profile.get('industry', 'general')
        industry_multiplier = self.risk_factors['industry'].get(industry, 1.0)
        if industry_multiplier != 1.0:
            factors.append(RiskFactor(
                name=f"Branche: {industry}",
                multiplier=industry_multiplier,
                description=f"Branchenspezifisches {'erhöhtes' if industry_multiplier > 1 else 'reduziertes'} Risiko"
            ))
        
        # Data sensitivity factor
        data_sensitivity = company_profile.get('data_sensitivity', 'basic')
        sensitivity_multiplier = self.risk_factors['data_sensitivity'].get(data_sensitivity, 1.0)
        if sensitivity_multiplier != 1.0:
            factors.append(RiskFactor(
                name=f"Datensensitivität: {data_sensitivity}",
                multiplier=sensitivity_multiplier,
                description=f"{'Erhöhtes' if sensitivity_multiplier > 1 else 'Reduziertes'} Risiko durch Datenarten"
            ))
        
        # Revenue factor
        revenue = company_profile.get('revenue', 'small')
        revenue_multiplier = self.risk_factors['revenue'].get(revenue, 1.0)
        if revenue_multiplier != 1.0:
            factors.append(RiskFactor(
                name=f"Umsatzgröße: {revenue}",
                multiplier=revenue_multiplier,
                description=f"Umsatzabhängiger {'Aufschlag' if revenue_multiplier > 1 else 'Rabatt'}"
            ))
        
        return factors
    
    def _calculate_total_multiplier(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate total risk multiplier from all factors"""
        if not risk_factors:
            return 1.0
        
        total_multiplier = 1.0
        for factor in risk_factors:
            total_multiplier *= factor.multiplier
        
        # Cap multiplier to reasonable ranges
        return max(0.3, min(3.0, total_multiplier))
    
    def _determine_risk_level(self, adjusted_risk: int, violation_count: int) -> str:
        """Determine overall risk level"""
        if adjusted_risk >= 15000 or violation_count >= 8:
            return "critical"
        elif adjusted_risk >= 8000 or violation_count >= 5:
            return "high"
        elif adjusted_risk >= 3000 or violation_count >= 3:
            return "medium"
        else:
            return "low"
    
    def _generate_risk_recommendations(self, violations: List[Dict[str, Any]], risk_level: str) -> List[str]:
        """Generate risk-based recommendations"""
        recommendations = []
        
        if risk_level == "critical":
            recommendations.extend([
                "🚨 SOFORTIGE MASSNAHMEN ERFORDERLICH",
                "Rechtliche Beratung umgehend einholen",
                "Kritische Verstöße binnen 24-48h beheben",
                "Experten-Service für schnelle Umsetzung empfohlen"
            ])
        elif risk_level == "high":
            recommendations.extend([
                "⚠️ HOHES ABMAHNRISIKO - schnelles Handeln nötig",
                "Verstöße innerhalb 1 Woche beheben",
                "KI-Automatisierung für schnelle Fixes nutzen",
                "Rechtliche Prüfung empfohlen"
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "🔶 Mittleres Risiko - Behebung empfohlen",
                "Verstöße innerhalb 2-4 Wochen angehen",
                "KI-Automatisierung ausreichend",
                "Präventive Maßnahmen umsetzen"
            ])
        else:
            recommendations.extend([
                "✅ Geringes Risiko - minimale Verbesserungen",
                "Verstöße bei nächster Website-Überarbeitung beheben",
                "Kontinuierliches Monitoring empfohlen"
            ])
        
        # Add specific violation-based recommendations
        critical_violations = [v for v in violations if v.get('severity') == 'critical']
        if critical_violations:
            recommendations.append(f"Priorität: {len(critical_violations)} kritische Verstöße zuerst beheben")
        
        return recommendations
    
    def _create_zero_risk_assessment(self) -> RiskAssessment:
        """Create assessment for websites with no violations"""
        return RiskAssessment(
            base_risk_euro=0,
            adjusted_risk_euro=0,
            risk_factors=[],
            violation_details=[],
            total_violations=0,
            risk_level="low",
            recommendations=[
                "✅ Keine kritischen Compliance-Verstöße gefunden",
                "Kontinuierliches Monitoring für neue Änderungen empfohlen",
                "Bei Website-Updates erneut prüfen lassen"
            ]
        )
    
    def get_violation_cost_breakdown(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed cost breakdown by violation type"""
        breakdown = {}
        total = 0
        
        for violation in violations:
            category = violation.get('category', 'Sonstige')
            risk = violation.get('risk_euro', 0)
            
            if category not in breakdown:
                breakdown[category] = {
                    'violations': 0,
                    'total_risk': 0,
                    'items': []
                }
            
            breakdown[category]['violations'] += 1
            breakdown[category]['total_risk'] += risk
            breakdown[category]['items'].append({
                'title': violation.get('title', ''),
                'risk_euro': risk,
                'severity': violation.get('severity', 'warning')
            })
            
            total += risk
        
        return {
            'categories': breakdown,
            'total_risk_euro': total,
            'highest_risk_category': max(breakdown.items(), key=lambda x: x[1]['total_risk'])[0] if breakdown else None
        }