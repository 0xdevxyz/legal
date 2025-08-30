"""ML Feature Extraction Engine
Extracts compliance-relevant features from website data
"""

import numpy as np
from typing import Dict, List, Any
from urllib.parse import urlparse
import re

class FeatureExtractor:
    """Extracts ML features from website data for compliance analysis"""
    
    def __init__(self):
        self.privacy_keywords = [
            'privacy', 'gdpr', 'cookie', 'consent', 'data protection',
            'datenschutz', 'cookies', 'privacy policy', 'terms'
        ]
        
    def extract_privacy_features(self, website_data: dict) -> np.ndarray:
        """Extract privacy-related features from website data"""
        features = [
            self._count_cookies(website_data),
            self._has_privacy_policy(website_data),
            self._count_forms(website_data),
            self._has_gdpr_keywords(website_data),
            self._count_third_party_scripts(website_data),
            self._has_cookie_consent_banner(website_data),
            self._count_tracking_pixels(website_data),
            self._has_opt_out_mechanism(website_data),
            self._count_external_links(website_data),
            self._has_data_protection_officer(website_data)
        ]
        return np.array(features, dtype=float)
    
    def extract_accessibility_features(self, website_data: dict) -> np.ndarray:
        """Extract accessibility features for WCAG compliance"""
        features = [
            self._image_alt_text_ratio(website_data),
            self._form_label_ratio(website_data),
            self._heading_structure_score(website_data),
            self._color_contrast_score(website_data),
            self._keyboard_navigation_score(website_data),
            self._aria_label_usage(website_data),
            self._video_caption_ratio(website_data),
            self._link_purpose_clarity(website_data)
        ]
        return np.array(features, dtype=float)
    
    def _count_cookies(self, data: dict) -> float:
        """Count and normalize cookie usage"""
        cookies = data.get('cookies', [])
        return min(len(cookies) / 10.0, 1.0)  # Normalize to [0,1]
    
    def _has_privacy_policy(self, data: dict) -> float:
        """Check for privacy policy presence"""
        content = data.get('content', '').lower()
        return 1.0 if any(keyword in content for keyword in ['privacy policy', 'datenschutz']) else 0.0
    
    def _count_forms(self, data: dict) -> float:
        """Count forms on page"""
        forms = data.get('forms', [])
        return min(len(forms) / 5.0, 1.0)
    
    def _has_gdpr_keywords(self, data: dict) -> float:
        """Check for GDPR-related keywords"""
        content = data.get('content', '').lower()
        gdpr_keywords = ['gdpr', 'general data protection', 'dsgvo']
        return 1.0 if any(keyword in content for keyword in gdpr_keywords) else 0.0
    
    def _count_third_party_scripts(self, data: dict) -> float:
        """Count third-party scripts"""
        scripts = data.get('third_party_scripts', [])
        return min(len(scripts) / 5.0, 1.0)
    
    def _has_cookie_consent_banner(self, data: dict) -> float:
        """Check for cookie consent banner"""
        content = data.get('content', '').lower()
        consent_keywords = ['cookie consent', 'accept cookies', 'cookie banner']
        return 1.0 if any(keyword in content for keyword in consent_keywords) else 0.0
    
    def _count_tracking_pixels(self, data: dict) -> float:
        """Count tracking pixels and analytics"""
        tracking = data.get('tracking_pixels', [])
        return min(len(tracking) / 3.0, 1.0)
    
    def _has_opt_out_mechanism(self, data: dict) -> float:
        """Check for opt-out mechanisms"""
        content = data.get('content', '').lower()
        opt_out_keywords = ['opt-out', 'unsubscribe', 'do not sell', 'reject all']
        return 1.0 if any(keyword in content for keyword in opt_out_keywords) else 0.0
    
    def _count_external_links(self, data: dict) -> float:
        """Count external links"""
        links = data.get('external_links', [])
        return min(len(links) / 10.0, 1.0)
    
    def _has_data_protection_officer(self, data: dict) -> float:
        """Check for DPO contact information"""
        content = data.get('content', '').lower()
        dpo_keywords = ['data protection officer', 'dpo', 'privacy officer']
        return 1.0 if any(keyword in content for keyword in dpo_keywords) else 0.0
    
    def _image_alt_text_ratio(self, data: dict) -> float:
        """Calculate ratio of images with alt text"""
        images = data.get('images', [])
        if not images:
            return 1.0
        
        with_alt = sum(1 for img in images if img.get('has_alt', False))
        return with_alt / len(images)
    
    def _form_label_ratio(self, data: dict) -> float:
        """Calculate ratio of form inputs with proper labels"""
        forms = data.get('forms', [])
        if not forms:
            return 1.0
        
        # Simplified calculation - in real implementation, parse form structure
        return 0.8  # Placeholder
    
    def _heading_structure_score(self, data: dict) -> float:
        """Score heading structure (H1, H2, etc.)"""
        content = data.get('content', '')
        h1_count = content.count('<h1')
        h2_count = content.count('<h2')
        
        # Good structure: exactly one H1, multiple H2s
        if h1_count == 1 and h2_count >= 1:
            return 1.0
        elif h1_count >= 1:
            return 0.7
        else:
            return 0.3
    
    def _color_contrast_score(self, data: dict) -> float:
        """Placeholder for color contrast analysis"""
        # This would require CSS analysis and color extraction
        return 0.8  # Placeholder score
    
    def _keyboard_navigation_score(self, data: dict) -> float:
        """Score keyboard navigation support"""
        content = data.get('content', '').lower()
        nav_indicators = ['tabindex', 'accesskey', 'role=', 'aria-']
        score = sum(1 for indicator in nav_indicators if indicator in content)
        return min(score / 4.0, 1.0)
    
    def _aria_label_usage(self, data: dict) -> float:
        """Check ARIA label usage"""
        content = data.get('content', '').lower()
        aria_count = content.count('aria-')
        return min(aria_count / 10.0, 1.0)
    
    def _video_caption_ratio(self, data: dict) -> float:
        """Calculate video caption compliance"""
        # Placeholder - would analyze video elements
        return 0.9
    
    def _link_purpose_clarity(self, data: dict) -> float:
        """Assess link purpose clarity"""
        links = data.get('links', [])
        if not links:
            return 1.0
        
        # Check for descriptive link text vs generic text
        generic_texts = ['click here', 'read more', 'learn more', 'here']
        descriptive_links = 0
        
        for link in links:
            text = link.get('text', '').lower().strip()
            if text and text not in generic_texts and len(text) > 3:
                descriptive_links += 1
        
        return descriptive_links / len(links) if links else 1.0