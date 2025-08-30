"""AI-Powered Compliance Recommendations Engine"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

class ComplianceRecommendationEngine:
    """Generates intelligent compliance recommendations using AI"""
    
    def __init__(self):
        self.recommendation_templates = self._load_recommendation_templates()
        self.priority_weights = {
            'critical': 100,
            'high': 75,
            'medium': 50,
            'low': 25
        }
        
    def generate_comprehensive_recommendations(self, 
                                            compliance_results: Dict[str, Any],
                                            website_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive compliance recommendations"""
        
        recommendations = {
            'gdpr_recommendations': [],
            'accessibility_recommendations': [],
            'ttdsg_recommendations': [],
            'general_recommendations': [],
            'priority_matrix': [],
            'implementation_timeline': [],
            'estimated_effort': {},
            'compliance_roadmap': []
        }
        
        # Generate GDPR recommendations
        if 'gdpr' in compliance_results:
            recommendations['gdpr_recommendations'] = self._generate_gdpr_recommendations(
                compliance_results['gdpr'], website_data
            )
        
        # Generate accessibility recommendations
        if 'accessibility' in compliance_results:
            recommendations['accessibility_recommendations'] = self._generate_accessibility_recommendations(
                compliance_results['accessibility'], website_data
            )
        
        # Generate TTDSG recommendations
        if 'ttdsg' in compliance_results:
            recommendations['ttdsg_recommendations'] = self._generate_ttdsg_recommendations(
                compliance_results['ttdsg'], website_data
            )
        
        # Create priority matrix
        all_recommendations = (
            recommendations['gdpr_recommendations'] +
            recommendations['accessibility_recommendations'] +
            recommendations['ttdsg_recommendations']
        )
        
        recommendations['priority_matrix'] = self._create_priority_matrix(all_recommendations)
        recommendations['implementation_timeline'] = self._create_implementation_timeline(all_recommendations)
        recommendations['estimated_effort'] = self._estimate_implementation_effort(all_recommendations)
        recommendations['compliance_roadmap'] = self._create_compliance_roadmap(all_recommendations)
        
        return recommendations
    
    def _generate_gdpr_recommendations(self, gdpr_results: Dict[str, Any], website_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate GDPR-specific recommendations"""
        
        recommendations = []
        score = gdpr_results.get('compliance_score', 0)
        
        # Cookie consent recommendations
        if score < 80:
            recommendations.append({
                'id': 'gdpr_cookie_consent',
                'title': 'Implement GDPR-Compliant Cookie Consent',
                'description': 'Add a comprehensive cookie consent banner with granular choices',
                'priority': 'critical',
                'compliance_area': 'gdpr',
                'implementation_steps': [
                    'Install cookie consent management platform',
                    'Configure cookie categories (necessary, analytics, marketing)',
                    'Implement reject all functionality',
                    'Add cookie policy page',
                    'Test consent flow on all devices'
                ],
                'estimated_hours': 16,
                'tools_needed': ['Cookie consent platform', 'Legal review'],
                'legal_risk': 'high',
                'impact_score': 90
            })
        
        # Privacy policy recommendations
        if 'detailed_analysis' in gdpr_results:
            policy_score = gdpr_results['detailed_analysis'].get('privacy_policy', {}).get('score', 0)
            if policy_score < 70:
                recommendations.append({
                    'id': 'gdpr_privacy_policy',
                    'title': 'Update Privacy Policy for GDPR Compliance',
                    'description': 'Enhance privacy policy with GDPR-required elements',
                    'priority': 'high',
                    'compliance_area': 'gdpr',
                    'implementation_steps': [
                        'Review current privacy policy gaps',
                        'Add data processing purposes and legal bases',
                        'Include data subject rights information',
                        'Add DPO contact information',
                        'Implement policy versioning and change notifications'
                    ],
                    'estimated_hours': 12,
                    'tools_needed': ['Legal consultant', 'Policy management system'],
                    'legal_risk': 'high',
                    'impact_score': 85
                })
        
        # Data processing transparency
        recommendations.append({
            'id': 'gdpr_data_mapping',
            'title': 'Create Data Processing Inventory',
            'description': 'Document all data processing activities and legal bases',
            'priority': 'medium',
            'compliance_area': 'gdpr',
            'implementation_steps': [
                'Audit all data collection points',
                'Map data flows and processing purposes',
                'Document legal bases for each processing activity',
                'Create data retention schedules',
                'Implement data processing records (Article 30)'
            ],
            'estimated_hours': 24,
            'tools_needed': ['Data mapping software', 'Privacy impact assessment tool'],
            'legal_risk': 'medium',
            'impact_score': 70
        })
        
        # User rights implementation
        if score < 75:
            recommendations.append({
                'id': 'gdpr_user_rights',
                'title': 'Implement Data Subject Rights Management',
                'description': 'Create system for handling GDPR data subject requests',
                'priority': 'high',
                'compliance_area': 'gdpr',
                'implementation_steps': [
                    'Design request submission forms',
                    'Implement identity verification process',
                    'Create data export functionality',
                    'Develop data deletion workflows',
                    'Set up request tracking system'
                ],
                'estimated_hours': 40,
                'tools_needed': ['User rights management platform', 'Identity verification service'],
                'legal_risk': 'high',
                'impact_score': 80
            })
        
        return recommendations
    
    def _generate_accessibility_recommendations(self, accessibility_results: Dict[str, Any], website_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate accessibility recommendations"""
        
        recommendations = []
        score = accessibility_results.get('compliance_score', 0)
        wcag_level = accessibility_results.get('wcag_level', 'Non-compliant')
        
        # Image alt text
        images = website_data.get('images', [])
        images_without_alt = [img for img in images if not img.get('has_alt', False)]
        
        if images_without_alt:
            recommendations.append({
                'id': 'accessibility_alt_text',
                'title': 'Add Alt Text to Images',
                'description': f'Add descriptive alt text to {len(images_without_alt)} images',
                'priority': 'high',
                'compliance_area': 'accessibility',
                'implementation_steps': [
                    'Audit all images on the website',
                    'Write descriptive alt text for each image',
                    'Implement alt text in CMS',
                    'Train content team on alt text best practices',
                    'Set up alt text validation in publishing workflow'
                ],
                'estimated_hours': len(images_without_alt) * 0.5,
                'tools_needed': ['Image audit tool', 'CMS alt text fields'],
                'legal_risk': 'medium',
                'impact_score': 60
            })
        
        # Keyboard navigation
        if score < 80:
            recommendations.append({
                'id': 'accessibility_keyboard_nav',
                'title': 'Improve Keyboard Navigation',
                'description': 'Ensure all interactive elements are keyboard accessible',
                'priority': 'high',
                'compliance_area': 'accessibility',
                'implementation_steps': [
                    'Audit tab order and focus indicators',
                    'Add skip navigation links',
                    'Implement proper ARIA labels',
                    'Test keyboard-only navigation',
                    'Fix focus traps in modals and dropdowns'
                ],
                'estimated_hours': 20,
                'tools_needed': ['Accessibility testing tools', 'Screen reader software'],
                'legal_risk': 'medium',
                'impact_score': 75
            })
        
        # Color contrast
        recommendations.append({
            'id': 'accessibility_color_contrast',
            'title': 'Improve Color Contrast',
            'description': 'Ensure all text meets WCAG AA color contrast requirements',
            'priority': 'medium',
            'compliance_area': 'accessibility',
            'implementation_steps': [
                'Audit current color combinations',
                'Test contrast ratios with automated tools',
                'Update design system with compliant colors',
                'Review and update existing content',
                'Implement contrast checking in design workflow'
            ],
            'estimated_hours': 16,
            'tools_needed': ['Color contrast analyzer', 'Design system updates'],
            'legal_risk': 'low',
            'impact_score': 50
        })
        
        return recommendations
    
    def _generate_ttdsg_recommendations(self, ttdsg_results: Dict[str, Any], website_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate TTDSG (German telecom law) recommendations"""
        
        recommendations = []
        
        recommendations.append({
            'id': 'ttdsg_cookie_banner',
            'title': 'TTDSG-Compliant Cookie Banner',
            'description': 'Implement cookie banner compliant with German TTDSG law',
            'priority': 'critical',
            'compliance_area': 'ttdsg',
            'implementation_steps': [
                'Review TTDSG requirements for cookie consent',
                'Implement cookie banner without cookie walls',
                'Ensure granular consent options',
                'Add German language support',
                'Document consent management processes'
            ],
            'estimated_hours': 12,
            'tools_needed': ['TTDSG-compliant consent tool', 'German legal review'],
            'legal_risk': 'high',
            'impact_score': 85
        })
        
        return recommendations
    
    def _create_priority_matrix(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create priority matrix based on impact and effort"""
        
        matrix = []
        
        for rec in recommendations:
            priority_score = self.priority_weights.get(rec.get('priority', 'medium'), 50)
            impact_score = rec.get('impact_score', 50)
            effort_score = 100 - min(100, rec.get('estimated_hours', 8) * 2)  # Lower hours = higher score
            
            overall_score = (priority_score * 0.4) + (impact_score * 0.4) + (effort_score * 0.2)
            
            matrix.append({
                'recommendation_id': rec['id'],
                'title': rec['title'],
                'priority_score': priority_score,
                'impact_score': impact_score,
                'effort_score': effort_score,
                'overall_score': overall_score,
                'quadrant': self._determine_quadrant(impact_score, effort_score)
            })
        
        # Sort by overall score
        matrix.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return matrix
    
    def _determine_quadrant(self, impact: float, effort: float) -> str:
        """Determine priority quadrant (Quick Wins, Major Projects, etc.)"""
        
        if impact >= 70 and effort >= 70:
            return 'Quick Wins'
        elif impact >= 70 and effort < 70:
            return 'Major Projects'
        elif impact < 70 and effort >= 70:
            return 'Fill-ins'
        else:
            return 'Thankless Tasks'
    
    def _create_implementation_timeline(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create implementation timeline based on priorities and dependencies"""
        
        timeline = []
        current_date = datetime.utcnow()
        
        # Sort by priority
        sorted_recs = sorted(recommendations, 
                           key=lambda x: self.priority_weights.get(x.get('priority', 'medium'), 50), 
                           reverse=True)
        
        cumulative_hours = 0
        for i, rec in enumerate(sorted_recs):
            hours = rec.get('estimated_hours', 8)
            
            # Assume 40 hours per week development capacity
            weeks_needed = max(1, hours / 40)
            
            start_date = current_date + timedelta(weeks=cumulative_hours/40)
            end_date = start_date + timedelta(weeks=weeks_needed)
            
            timeline.append({
                'recommendation_id': rec['id'],
                'title': rec['title'],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_weeks': weeks_needed,
                'phase': self._determine_phase(i, len(sorted_recs))
            })
            
            cumulative_hours += hours
        
        return timeline
    
    def _determine_phase(self, index: int, total: int) -> str:
        """Determine implementation phase"""
        
        if index < total * 0.3:
            return 'Phase 1: Critical Issues'
        elif index < total * 0.7:
            return 'Phase 2: Important Improvements'
        else:
            return 'Phase 3: Enhancement & Optimization'
    
    def _estimate_implementation_effort(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate overall implementation effort"""
        
        total_hours = sum(rec.get('estimated_hours', 8) for rec in recommendations)
        
        effort_by_area = {}
        for rec in recommendations:
            area = rec.get('compliance_area', 'general')
            if area not in effort_by_area:
                effort_by_area[area] = 0
            effort_by_area[area] += rec.get('estimated_hours', 8)
        
        return {
            'total_hours': total_hours,
            'total_weeks': max(1, total_hours / 40),
            'effort_by_area': effort_by_area,
            'estimated_cost': total_hours * 100,  # $100 per hour estimate
            'team_size_recommendation': max(1, total_hours / 160),  # 4 weeks per person
            'completion_timeline': f"{max(1, total_hours / 40):.1f} weeks with dedicated team"
        }
    
    def _create_compliance_roadmap(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create high-level compliance roadmap"""
        
        roadmap = [
            {
                'milestone': 'Quick Compliance Wins',
                'timeline': '2-4 weeks',
                'description': 'Address critical GDPR and accessibility issues',
                'deliverables': ['Cookie consent implementation', 'Privacy policy updates', 'Critical accessibility fixes'],
                'success_metrics': ['GDPR compliance score > 80%', 'Basic WCAG AA compliance']
            },
            {
                'milestone': 'Full Legal Compliance',
                'timeline': '6-8 weeks', 
                'description': 'Achieve comprehensive GDPR and TTDSG compliance',
                'deliverables': ['Complete data mapping', 'User rights management', 'TTDSG compliance'],
                'success_metrics': ['GDPR compliance score > 90%', 'TTDSG compliance achieved']
            },
            {
                'milestone': 'Accessibility Excellence',
                'timeline': '10-12 weeks',
                'description': 'Achieve WCAG AA+ accessibility standards',
                'deliverables': ['Full keyboard navigation', 'Screen reader compatibility', 'Color contrast compliance'],
                'success_metrics': ['WCAG AA compliance achieved', 'Accessibility score > 90%']
            },
            {
                'milestone': 'Ongoing Monitoring',
                'timeline': 'Continuous',
                'description': 'Maintain compliance through regular monitoring',
                'deliverables': ['Automated compliance monitoring', 'Regular audits', 'Team training'],
                'success_metrics': ['Monthly compliance reports', '95%+ sustained compliance scores']
            }
        ]
        
        return roadmap
    
    def _load_recommendation_templates(self) -> Dict[str, Any]:
        """Load recommendation templates (would be from database/file in production)"""
        
        return {
            'gdpr': {
                'cookie_consent': 'Implement comprehensive cookie consent management',
                'privacy_policy': 'Update privacy policy for GDPR compliance',
                'user_rights': 'Implement data subject rights management',
                'data_mapping': 'Create comprehensive data processing inventory'
            },
            'accessibility': {
                'alt_text': 'Add alt text to all images',
                'keyboard_nav': 'Improve keyboard navigation',
                'color_contrast': 'Fix color contrast issues',
                'heading_structure': 'Improve heading hierarchy'
            },
            'ttdsg': {
                'cookie_banner': 'Implement TTDSG-compliant cookie banner',
                'consent_management': 'Update consent management for German law'
            }
        }