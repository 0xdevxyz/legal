"""Natural Language Processing for Compliance Text Analysis"""

import re
from typing import Dict, List, Any, Optional
import spacy
from textblob import TextBlob
import logging

logger = logging.getLogger(__name__)

class ComplianceNLP:
    """NLP processor for compliance document analysis"""
    
    def __init__(self):
        self.privacy_keywords = {
            'gdpr': ['gdpr', 'general data protection', 'dsgvo', 'data protection regulation'],
            'cookies': ['cookie', 'tracking', 'analytics', 'pixels', 'beacons'],
            'consent': ['consent', 'agreement', 'permission', 'opt-in', 'opt-out'],
            'rights': ['access', 'rectification', 'erasure', 'portability', 'object'],
            'processing': ['processing', 'collection', 'storage', 'transfer', 'sharing']
        }
        
    def analyze_privacy_policy(self, text: str) -> Dict[str, Any]:
        """Analyze privacy policy text for GDPR compliance"""
        
        analysis = {
            'word_count': len(text.split()),
            'readability_score': self._calculate_readability(text),
            'gdpr_coverage': self._analyze_gdpr_coverage(text),
            'language_clarity': self._assess_language_clarity(text),
            'legal_completeness': self._check_legal_completeness(text),
            'sentiment_score': self._analyze_sentiment(text)
        }
        
        return analysis
    
    def extract_data_practices(self, text: str) -> Dict[str, List[str]]:
        """Extract data collection and processing practices"""
        
        practices = {
            'data_collected': self._extract_data_types(text),
            'processing_purposes': self._extract_purposes(text),
            'third_parties': self._extract_third_parties(text),
            'retention_periods': self._extract_retention_info(text),
            'user_rights': self._extract_user_rights(text)
        }
        
        return practices
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate text readability score (Flesch Reading Ease)"""
        
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        syllables = self._count_syllables(text)
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Flesch Reading Ease Score
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0, min(100, score))
    
    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count in text"""
        
        text = text.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        
        for word in text.split():
            word = re.sub(r'[^a-z]', '', word)
            if word:
                syllables_in_word = 0
                prev_was_vowel = False
                
                for char in word:
                    if char in vowels:
                        if not prev_was_vowel:
                            syllables_in_word += 1
                        prev_was_vowel = True
                    else:
                        prev_was_vowel = False
                
                # Adjust for silent e
                if word.endswith('e'):
                    syllables_in_word = max(1, syllables_in_word - 1)
                
                syllable_count += max(1, syllables_in_word)
        
        return syllable_count
    
    def _analyze_gdpr_coverage(self, text: str) -> Dict[str, bool]:
        """Check coverage of key GDPR topics"""
        
        text_lower = text.lower()
        
        coverage = {
            'mentions_gdpr': any(keyword in text_lower for keyword in self.privacy_keywords['gdpr']),
            'data_processing_purpose': 'purpose' in text_lower and 'processing' in text_lower,
            'legal_basis': 'legal basis' in text_lower or 'lawful basis' in text_lower,
            'user_rights': any(right in text_lower for right in self.privacy_keywords['rights']),
            'data_retention': 'retention' in text_lower or 'delete' in text_lower,
            'data_sharing': 'share' in text_lower or 'third party' in text_lower,
            'contact_info': 'contact' in text_lower and ('dpo' in text_lower or 'data protection officer' in text_lower),
            'consent_mechanism': any(keyword in text_lower for keyword in self.privacy_keywords['consent'])
        }
        
        return coverage
    
    def _assess_language_clarity(self, text: str) -> Dict[str, Any]:
        """Assess language clarity and complexity"""
        
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        avg_sentence_length = len(words) / max(1, len([s for s in sentences if s.strip()]))
        
        # Count complex words (more than 2 syllables)
        complex_words = 0
        for word in words:
            if self._count_syllables(word) > 2:
                complex_words += 1
        
        complex_word_ratio = complex_words / max(1, len(words))
        
        return {
            'average_sentence_length': avg_sentence_length,
            'complex_word_ratio': complex_word_ratio,
            'clarity_score': max(0, 100 - (avg_sentence_length * 2) - (complex_word_ratio * 100))
        }
    
    def _check_legal_completeness(self, text: str) -> Dict[str, bool]:
        """Check for required legal elements"""
        
        text_lower = text.lower()
        
        required_elements = {
            'data_controller_identity': 'controller' in text_lower or 'responsible' in text_lower,
            'processing_purposes': 'purpose' in text_lower,
            'legal_basis_specified': 'legal basis' in text_lower,
            'recipient_categories': 'recipient' in text_lower or 'share' in text_lower,
            'retention_criteria': 'retention' in text_lower or 'keep' in text_lower or 'delete' in text_lower,
            'individual_rights': any(right in text_lower for right in ['access', 'rectification', 'erasure']),
            'complaint_right': 'supervisory authority' in text_lower or 'complaint' in text_lower,
            'automated_decision_making': 'automated' in text_lower or 'profiling' in text_lower
        }
        
        return required_elements
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of privacy policy (trustworthiness)"""
        
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def _extract_data_types(self, text: str) -> List[str]:
        """Extract types of data mentioned"""
        
        data_types = []
        text_lower = text.lower()
        
        data_patterns = {
            'personal_information': ['name', 'address', 'email', 'phone', 'personal information'],
            'device_information': ['device', 'browser', 'ip address', 'user agent'],
            'usage_data': ['usage', 'behavior', 'interaction', 'activity'],
            'location_data': ['location', 'gps', 'geolocation'],
            'financial_data': ['payment', 'credit card', 'financial', 'billing'],
            'biometric_data': ['biometric', 'fingerprint', 'facial recognition']
        }
        
        for category, patterns in data_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                data_types.append(category)
        
        return data_types
    
    def _extract_purposes(self, text: str) -> List[str]:
        """Extract processing purposes mentioned"""
        
        purposes = []
        text_lower = text.lower()
        
        purpose_patterns = {
            'service_provision': ['provide service', 'deliver', 'fulfill'],
            'communication': ['communicate', 'contact', 'respond', 'notify'],
            'improvement': ['improve', 'enhance', 'develop', 'optimize'],
            'marketing': ['marketing', 'advertising', 'promotional', 'newsletter'],
            'analytics': ['analytics', 'analyze', 'statistics', 'insights'],
            'security': ['security', 'fraud', 'protect', 'prevent'],
            'legal_compliance': ['legal', 'compliance', 'regulatory', 'obligation']
        }
        
        for purpose, patterns in purpose_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                purposes.append(purpose)
        
        return purposes
    
    def _extract_third_parties(self, text: str) -> List[str]:
        """Extract mentioned third parties"""
        
        third_parties = []
        
        # Common third-party service patterns
        services = ['google', 'facebook', 'analytics', 'advertising', 'payment processor', 
                   'cloud provider', 'service provider', 'partner', 'affiliate']
        
        text_lower = text.lower()
        for service in services:
            if service in text_lower:
                third_parties.append(service)
        
        return third_parties
    
    def _extract_retention_info(self, text: str) -> List[str]:
        """Extract data retention information"""
        
        retention_info = []
        
        # Look for time-related patterns
        time_patterns = [
            r'\d+\s*(year|month|day)s?',
            r'as long as',
            r'until',
            r'permanently',
            r'indefinitely'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                retention_info.append(context)
        
        return retention_info
    
    def _extract_user_rights(self, text: str) -> List[str]:
        """Extract mentioned user rights"""
        
        rights = []
        text_lower = text.lower()
        
        right_keywords = {
            'access': ['access', 'obtain copy', 'request information'],
            'rectification': ['correct', 'rectify', 'update', 'modify'],
            'erasure': ['delete', 'remove', 'erase', 'right to be forgotten'],
            'portability': ['portability', 'transfer', 'export'],
            'object': ['object', 'opt-out', 'withdraw consent'],
            'restrict': ['restrict', 'limit processing']
        }
        
        for right, keywords in right_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                rights.append(right)
        
        return rights