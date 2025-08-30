"""ML Prediction Service
Real-time compliance predictions using trained models
"""

import numpy as np
import joblib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CompliancePredictionService:
    """Real-time compliance prediction service"""
    
    def __init__(self, model_directory: str = "ml_models"):
        self.model_directory = Path(model_directory)
        self.models = {}
        self.feature_extractors = {}
        self.model_metadata = {}
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all available trained models"""
        try:
            model_files = {
                'gdpr_classifier': 'gdpr_compliance_model.pkl',
                'ttdsg_classifier': 'ttdsg_compliance_model.pkl', 
                'accessibility_classifier': 'accessibility_model.pkl',
                'privacy_scorer': 'privacy_score_model.pkl',
                'risk_assessor': 'risk_assessment_model.pkl'
            }
            
            for model_name, filename in model_files.items():
                model_path = self.model_directory / filename
                if model_path.exists():
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"Loaded model: {model_name}")
                else:
                    logger.warning(f"Model file not found: {model_path}")
                    
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def predict_gdpr_compliance(self, website_data: dict) -> Dict[str, Any]:
        """Predict GDPR compliance score and details"""
        
        if 'gdpr_classifier' not in self.models:
            return self._fallback_gdpr_prediction(website_data)
        
        try:
            # Extract features
            features = self._extract_gdpr_features(website_data)
            
            # Get model predictions
            model = self.models['gdpr_classifier']
            compliance_prob = model.predict_proba([features])[0]
            compliance_prediction = model.predict([features])[0]
            
            # Calculate detailed scores
            detailed_analysis = self._analyze_gdpr_components(website_data, features)
            
            result = {
                "compliance_score": float(compliance_prob[1] * 100),  # Probability of compliance
                "status": "compliant" if compliance_prediction == 1 else "non_compliant",
                "confidence": float(np.max(compliance_prob)),
                "prediction_date": datetime.utcnow().isoformat(),
                "detailed_analysis": detailed_analysis,
                "recommendations": self._generate_gdpr_recommendations(detailed_analysis),
                "risk_level": self._assess_gdpr_risk(compliance_prob[1])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"GDPR prediction failed: {e}")
            return self._fallback_gdpr_prediction(website_data)
    
    def predict_accessibility_compliance(self, website_data: dict) -> Dict[str, Any]:
        """Predict accessibility compliance (WCAG 2.1)"""
        
        if 'accessibility_classifier' not in self.models:
            return self._fallback_accessibility_prediction(website_data)
        
        try:
            features = self._extract_accessibility_features(website_data)
            
            model = self.models['accessibility_classifier']
            accessibility_prob = model.predict_proba([features])[0]
            accessibility_prediction = model.predict([features])[0]
            
            # Determine WCAG level
            wcag_level = self._determine_wcag_level(accessibility_prob[1])
            
            result = {
                "compliance_score": float(accessibility_prob[1] * 100),
                "wcag_level": wcag_level,
                "status": "compliant" if accessibility_prediction == 1 else "non_compliant",
                "confidence": float(np.max(accessibility_prob)),
                "prediction_date": datetime.utcnow().isoformat(),
                "accessibility_issues": self._identify_accessibility_issues(website_data),
                "recommendations": self._generate_accessibility_recommendations(website_data)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Accessibility prediction failed: {e}")
            return self._fallback_accessibility_prediction(website_data)
    
    def predict_overall_compliance_risk(self, website_data: dict) -> Dict[str, Any]:
        """Predict overall compliance risk across all regulations"""
        
        try:
            # Get individual predictions
            gdpr_result = self.predict_gdpr_compliance(website_data)
            accessibility_result = self.predict_accessibility_compliance(website_data)
            
            # Calculate weighted overall score
            weights = {
                'gdpr': 0.4,
                'accessibility': 0.3,
                'ttdsg': 0.3
            }
            
            overall_score = (
                gdpr_result['compliance_score'] * weights['gdpr'] +
                accessibility_result['compliance_score'] * weights['accessibility'] +
                87.5 * weights['ttdsg']  # TTDSG placeholder
            )\n            \n            # Determine overall risk level\n            risk_level = self._calculate_overall_risk_level(overall_score)\n            \n            result = {\n                \"overall_compliance_score\": round(overall_score, 1),\n                \"risk_level\": risk_level,\n                \"individual_scores\": {\n                    \"gdpr\": gdpr_result['compliance_score'],\n                    \"accessibility\": accessibility_result['compliance_score'],\n                    \"ttdsg\": 87.5  # Placeholder\n                },\n                \"prediction_date\": datetime.utcnow().isoformat(),\n                \"priority_actions\": self._identify_priority_actions({\n                    \"gdpr\": gdpr_result,\n                    \"accessibility\": accessibility_result\n                }),\n                \"compliance_trend\": \"stable\",  # Would be calculated from historical data\n                \"next_review_date\": self._calculate_next_review_date(risk_level)\n            }\n            \n            return result\n            \n        except Exception as e:\n            logger.error(f\"Overall risk prediction failed: {e}\")\n            return self._fallback_risk_prediction()\n    \n    def batch_predict(self, websites_data: List[dict]) -> List[Dict[str, Any]]:\n        \"\"\"Batch prediction for multiple websites\"\"\"\n        results = []\n        \n        for website_data in websites_data:\n            try:\n                prediction = self.predict_overall_compliance_risk(website_data)\n                prediction['website_url'] = website_data.get('url', 'unknown')\n                results.append(prediction)\n            except Exception as e:\n                logger.error(f\"Batch prediction failed for {website_data.get('url')}: {e}\")\n                results.append({\n                    'website_url': website_data.get('url', 'unknown'),\n                    'error': str(e),\n                    'status': 'prediction_failed'\n                })\n        \n        return results\n    \n    def _extract_gdpr_features(self, website_data: dict) -> np.ndarray:\n        \"\"\"Extract GDPR-specific features\"\"\"\n        # Use the FeatureExtractor from features.py\n        from .features import FeatureExtractor\n        \n        extractor = FeatureExtractor()\n        return extractor.extract_privacy_features(website_data)\n    \n    def _extract_accessibility_features(self, website_data: dict) -> np.ndarray:\n        \"\"\"Extract accessibility-specific features\"\"\"\n        from .features import FeatureExtractor\n        \n        extractor = FeatureExtractor()\n        return extractor.extract_accessibility_features(website_data)\n    \n    def _analyze_gdpr_components(self, website_data: dict, features: np.ndarray) -> Dict[str, Any]:\n        \"\"\"Analyze individual GDPR components\"\"\"\n        content = website_data.get('content', '').lower()\n        \n        return {\n            \"cookie_consent\": {\n                \"present\": \"cookie\" in content and \"consent\" in content,\n                \"score\": 85 if \"accept\" in content and \"reject\" in content else 45,\n                \"compliant\": \"accept\" in content and \"reject\" in content\n            },\n            \"privacy_policy\": {\n                \"present\": \"privacy policy\" in content or \"datenschutz\" in content,\n                \"score\": 90 if \"gdpr\" in content else 60,\n                \"compliant\": \"gdpr\" in content and \"data processing\" in content\n            },\n            \"data_processing_transparency\": {\n                \"score\": 80 if \"legal basis\" in content else 50,\n                \"compliant\": \"purpose\" in content and \"legal basis\" in content\n            },\n            \"user_rights\": {\n                \"score\": 75 if \"deletion\" in content else 40,\n                \"compliant\": \"access\" in content and \"deletion\" in content\n            }\n        }\n    \n    def _generate_gdpr_recommendations(self, analysis: Dict[str, Any]) -> List[str]:\n        \"\"\"Generate GDPR compliance recommendations\"\"\"\n        recommendations = []\n        \n        if not analysis[\"cookie_consent\"][\"compliant\"]:\n            recommendations.append(\"Implement comprehensive cookie consent banner with accept/reject options\")\n        \n        if not analysis[\"privacy_policy\"][\"compliant\"]:\n            recommendations.append(\"Update privacy policy to include GDPR-compliant data processing information\")\n        \n        if not analysis[\"data_processing_transparency\"][\"compliant\"]:\n            recommendations.append(\"Clearly specify legal basis and purpose for data processing\")\n        \n        if not analysis[\"user_rights\"][\"compliant\"]:\n            recommendations.append(\"Implement user rights management (access, rectification, erasure)\")\n        \n        return recommendations\n    \n    def _assess_gdpr_risk(self, compliance_probability: float) -> str:\n        \"\"\"Assess GDPR compliance risk level\"\"\"\n        if compliance_probability >= 0.85:\n            return \"low\"\n        elif compliance_probability >= 0.65:\n            return \"medium\"\n        else:\n            return \"high\"\n    \n    def _determine_wcag_level(self, accessibility_score: float) -> str:\n        \"\"\"Determine WCAG compliance level\"\"\"\n        if accessibility_score >= 0.95:\n            return \"AAA\"\n        elif accessibility_score >= 0.85:\n            return \"AA\"\n        elif accessibility_score >= 0.70:\n            return \"A\"\n        else:\n            return \"Non-compliant\"\n    \n    def _identify_accessibility_issues(self, website_data: dict) -> List[Dict[str, Any]]:\n        \"\"\"Identify specific accessibility issues\"\"\"\n        issues = []\n        \n        images = website_data.get('images', [])\n        images_without_alt = [img for img in images if not img.get('has_alt', False)]\n        \n        if images_without_alt:\n            issues.append({\n                \"type\": \"missing_alt_text\",\n                \"severity\": \"medium\",\n                \"count\": len(images_without_alt),\n                \"description\": f\"{len(images_without_alt)} images missing alt text\"\n            })\n        \n        # Check for proper heading structure\n        content = website_data.get('content', '')\n        h1_count = content.count('<h1')\n        if h1_count == 0:\n            issues.append({\n                \"type\": \"missing_h1\",\n                \"severity\": \"high\",\n                \"description\": \"No H1 heading found on page\"\n            })\n        elif h1_count > 1:\n            issues.append({\n                \"type\": \"multiple_h1\",\n                \"severity\": \"medium\",\n                \"description\": f\"Multiple H1 headings found ({h1_count})\"\n            })\n        \n        return issues\n    \n    def _generate_accessibility_recommendations(self, website_data: dict) -> List[str]:\n        \"\"\"Generate accessibility recommendations\"\"\"\n        recommendations = []\n        issues = self._identify_accessibility_issues(website_data)\n        \n        for issue in issues:\n            if issue[\"type\"] == \"missing_alt_text\":\n                recommendations.append(\"Add descriptive alt text to all images for screen readers\")\n            elif issue[\"type\"] == \"missing_h1\":\n                recommendations.append(\"Add a descriptive H1 heading to establish page structure\")\n            elif issue[\"type\"] == \"multiple_h1\":\n                recommendations.append(\"Use only one H1 heading per page for proper document structure\")\n        \n        # General recommendations\n        recommendations.extend([\n            \"Ensure keyboard navigation works for all interactive elements\",\n            \"Verify color contrast meets WCAG AA standards (4.5:1 ratio)\",\n            \"Add ARIA labels where appropriate for better screen reader support\"\n        ])\n        \n        return recommendations\n    \n    def _calculate_overall_risk_level(self, overall_score: float) -> str:\n        \"\"\"Calculate overall compliance risk level\"\"\"\n        if overall_score >= 90:\n            return \"very_low\"\n        elif overall_score >= 80:\n            return \"low\"\n        elif overall_score >= 65:\n            return \"medium\"\n        elif overall_score >= 50:\n            return \"high\"\n        else:\n            return \"very_high\"\n    \n    def _identify_priority_actions(self, compliance_results: Dict[str, Any]) -> List[str]:\n        \"\"\"Identify priority actions based on compliance gaps\"\"\"\n        actions = []\n        \n        # Check GDPR issues\n        gdpr_score = compliance_results.get('gdpr', {}).get('compliance_score', 0)\n        if gdpr_score < 75:\n            actions.append(\"Address GDPR compliance gaps - high legal risk\")\n        \n        # Check accessibility issues\n        acc_score = compliance_results.get('accessibility', {}).get('compliance_score', 0)\n        if acc_score < 70:\n            actions.append(\"Improve website accessibility - impacts user experience\")\n        \n        # Add general recommendations\n        if not actions:\n            actions.append(\"Maintain current compliance levels through regular monitoring\")\n        \n        return actions\n    \n    def _calculate_next_review_date(self, risk_level: str) -> str:\n        \"\"\"Calculate when next compliance review should occur\"\"\"\n        from datetime import datetime, timedelta\n        \n        review_intervals = {\n            \"very_high\": 30,    # 1 month\n            \"high\": 90,         # 3 months  \n            \"medium\": 180,      # 6 months\n            \"low\": 365,         # 1 year\n            \"very_low\": 365     # 1 year\n        }\n        \n        days = review_intervals.get(risk_level, 180)\n        next_review = datetime.utcnow() + timedelta(days=days)\n        return next_review.isoformat()\n    \n    def _fallback_gdpr_prediction(self, website_data: dict) -> Dict[str, Any]:\n        \"\"\"Fallback GDPR prediction when model is not available\"\"\"\n        content = website_data.get('content', '').lower()\n        \n        # Simple rule-based scoring\n        score = 50  # Base score\n        if 'privacy policy' in content or 'datenschutz' in content:\n            score += 15\n        if 'cookie' in content and 'consent' in content:\n            score += 15\n        if 'gdpr' in content or 'dsgvo' in content:\n            score += 20\n        \n        return {\n            \"compliance_score\": min(score, 100),\n            \"status\": \"compliant\" if score >= 75 else \"non_compliant\",\n            \"confidence\": 0.7,\n            \"prediction_date\": datetime.utcnow().isoformat(),\n            \"method\": \"rule_based_fallback\",\n            \"recommendations\": [\"Enable ML models for more accurate predictions\"]\n        }\n    \n    def _fallback_accessibility_prediction(self, website_data: dict) -> Dict[str, Any]:\n        \"\"\"Fallback accessibility prediction\"\"\"\n        images = website_data.get('images', [])\n        images_with_alt = sum(1 for img in images if img.get('has_alt', False))\n        \n        score = 60  # Base score\n        if images:\n            alt_ratio = images_with_alt / len(images)\n            score += alt_ratio * 30\n        else:\n            score += 20\n        \n        return {\n            \"compliance_score\": min(score, 100),\n            \"wcag_level\": \"A\" if score >= 70 else \"Non-compliant\",\n            \"status\": \"compliant\" if score >= 70 else \"non_compliant\",\n            \"confidence\": 0.6,\n            \"prediction_date\": datetime.utcnow().isoformat(),\n            \"method\": \"rule_based_fallback\"\n        }\n    \n    def _fallback_risk_prediction(self) -> Dict[str, Any]:\n        \"\"\"Fallback overall risk prediction\"\"\"\n        return {\n            \"overall_compliance_score\": 70.0,\n            \"risk_level\": \"medium\",\n            \"prediction_date\": datetime.utcnow().isoformat(),\n            \"method\": \"fallback\",\n            \"recommendations\": [\"Enable ML models for accurate risk assessment\"]\n        }