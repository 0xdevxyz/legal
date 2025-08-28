"""
A/B Testing System - Landing Page Optimization
Professional A/B testing framework for Complyo landing pages
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class VariantType(Enum):
    CONTROL = "control"
    VARIANT = "variant"

class MetricType(Enum):
    CONVERSION_RATE = "conversion_rate"
    CLICK_THROUGH_RATE = "click_through_rate"
    BOUNCE_RATE = "bounce_rate"
    TIME_ON_PAGE = "time_on_page"
    FORM_COMPLETION = "form_completion"
    SIGNUP_RATE = "signup_rate"

@dataclass
class TestVariant:
    """A/B test variant configuration"""
    variant_id: str
    name: str
    variant_type: VariantType
    traffic_allocation: float  # Percentage of traffic (0.0 - 1.0)
    configuration: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TestMetric:
    """Test success metric definition"""
    metric_id: str
    name: str
    metric_type: MetricType
    goal_value: Optional[float] = None
    is_primary: bool = False
    description: Optional[str] = None

@dataclass
class ABTest:
    """A/B test configuration"""
    test_id: str
    name: str
    description: str
    page_path: str  # Which page to test
    status: TestStatus
    variants: List[TestVariant]
    metrics: List[TestMetric]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sample_size_target: Optional[int] = None
    confidence_level: float = 0.95
    statistical_power: float = 0.8
    created_by: str = ""
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class TestEvent:
    """Individual test event/interaction"""
    event_id: str
    test_id: str
    variant_id: str
    user_id: Optional[str]
    session_id: str
    event_type: str  # page_view, conversion, click, etc.
    event_data: Dict[str, Any]
    timestamp: datetime
    ip_hash: Optional[str] = None
    user_agent_hash: Optional[str] = None
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class TestResults:
    """A/B test statistical results"""
    test_id: str
    variant_results: Dict[str, Dict[str, Any]]
    statistical_significance: Dict[str, bool]
    confidence_intervals: Dict[str, Dict[str, float]]
    recommendations: List[str]
    winner_variant: Optional[str] = None
    calculated_at: datetime = None
    
    def __post_init__(self):
        if self.calculated_at is None:
            self.calculated_at = datetime.now()

class ABTestingManager:
    """Comprehensive A/B testing system"""
    
    def __init__(self):
        """Initialize A/B testing manager"""
        
        # Storage (in production: use database)
        self.tests: Dict[str, ABTest] = {}
        self.events: Dict[str, List[TestEvent]] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user -> test -> variant
        self.session_assignments: Dict[str, Dict[str, str]] = {}  # session -> test -> variant
        
        # Test configurations for Complyo
        self._create_default_tests()
        
        logger.info("🧪 A/B Testing Manager initialized")
    
    def _create_default_tests(self):
        """Create default A/B tests for Complyo"""
        
        # Landing page hero section test
        hero_test = ABTest(
            test_id=str(uuid.uuid4()),
            name="Landing Page Hero Optimization",
            description="Test different hero section designs for conversion optimization",
            page_path="/",
            status=TestStatus.RUNNING,
            variants=[
                TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name="Original Hero",
                    variant_type=VariantType.CONTROL,
                    traffic_allocation=0.5,
                    configuration={
                        "hero_title": "Website-Compliance leicht gemacht",
                        "hero_subtitle": "DSGVO-konforme Websites in wenigen Minuten",
                        "cta_text": "Kostenlos scannen",
                        "cta_color": "#3B82F6",
                        "background_image": "/hero-bg-1.jpg"
                    }
                ),
                TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name="Urgency Hero",
                    variant_type=VariantType.VARIANT,
                    traffic_allocation=0.5,
                    configuration={
                        "hero_title": "Vermeiden Sie teure Abmahnungen",
                        "hero_subtitle": "Bis zu 20 Mio. € Bußgeld bei DSGVO-Verstößen",
                        "cta_text": "Jetzt prüfen lassen",
                        "cta_color": "#EF4444",
                        "background_image": "/hero-bg-2.jpg",
                        "urgency_badge": "Bereits 1.247 Websites geschützt"
                    }
                )
            ],
            metrics=[
                TestMetric(
                    metric_id=str(uuid.uuid4()),
                    name="Homepage Conversion Rate",
                    metric_type=MetricType.CONVERSION_RATE,
                    goal_value=0.08,
                    is_primary=True,
                    description="Percentage of visitors who start a scan"
                ),
                TestMetric(
                    metric_id=str(uuid.uuid4()),
                    name="Click-Through Rate",
                    metric_type=MetricType.CLICK_THROUGH_RATE,
                    description="CTA button clicks / page views"
                )
            ],
            sample_size_target=1000,
            created_by="system"
        )
        
        # Pricing page test
        pricing_test = ABTest(
            test_id=str(uuid.uuid4()),
            name="Pricing Strategy Test",
            description="Test different pricing presentations and strategies",
            page_path="/pricing",
            status=TestStatus.RUNNING,
            variants=[
                TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name="Standard Pricing",
                    variant_type=VariantType.CONTROL,
                    traffic_allocation=0.33,
                    configuration={
                        "ai_price": 39,
                        "expert_price": 2000,
                        "currency": "EUR",
                        "billing_period": "month",
                        "show_discount": False
                    }
                ),
                TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name="Anchored Pricing",
                    variant_type=VariantType.VARIANT,
                    traffic_allocation=0.33,
                    configuration={
                        "ai_price": 39,
                        "expert_price": 2000,
                        "currency": "EUR",
                        "billing_period": "month",
                        "show_discount": True,
                        "original_ai_price": 49,
                        "original_expert_price": 2500
                    }
                ),
                TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name="Value-Based Pricing",
                    variant_type=VariantType.VARIANT,
                    traffic_allocation=0.34,
                    configuration={
                        "ai_price": 39,
                        "expert_price": 2000,
                        "currency": "EUR",
                        "billing_period": "month",
                        "show_savings": True,
                        "potential_savings": "Bis zu 20.000€ an Bußgeldern sparen",
                        "roi_highlight": True
                    }
                )
            ],
            metrics=[
                TestMetric(
                    metric_id=str(uuid.uuid4()),
                    name="Purchase Conversion",
                    metric_type=MetricType.CONVERSION_RATE,
                    goal_value=0.12,
                    is_primary=True,
                    description="Percentage of pricing page visitors who purchase"
                )
            ],
            sample_size_target=800,
            created_by="system"
        )
        
        # Form optimization test
        form_test = ABTest(
            test_id=str(uuid.uuid4()),
            name="Signup Form Optimization",
            description="Test different form designs and field requirements",
            page_path="/signup",
            status=TestStatus.DRAFT,
            variants=[
                TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name="Standard Form",
                    variant_type=VariantType.CONTROL,
                    traffic_allocation=0.5,
                    configuration={
                        "fields": ["email", "password", "first_name", "last_name", "company"],
                        "form_title": "Kostenlosen Account erstellen",
                        "submit_button": "Account erstellen",
                        "show_benefits": False
                    }
                ),
                TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name="Minimal Form",
                    variant_type=VariantType.VARIANT,
                    traffic_allocation=0.5,
                    configuration={
                        "fields": ["email", "password"],
                        "form_title": "Sofort loslegen",
                        "submit_button": "Jetzt starten",
                        "show_benefits": True,
                        "benefits": ["✓ 7 Tage kostenlos", "✓ Keine Kreditkarte", "✓ Sofort einsatzbereit"]
                    }
                )
            ],
            metrics=[
                TestMetric(
                    metric_id=str(uuid.uuid4()),
                    name="Form Completion Rate",
                    metric_type=MetricType.FORM_COMPLETION,
                    goal_value=0.65,
                    is_primary=True,
                    description="Percentage of form starts that complete successfully"
                )
            ],
            sample_size_target=500,
            created_by="system"
        )
        
        # Store tests
        for test in [hero_test, pricing_test, form_test]:
            self.tests[test.test_id] = test
            self.events[test.test_id] = []
        
        logger.info(f"🧪 Created {len(self.tests)} default A/B tests")
    
    def get_variant_for_user(self, test_id: str, user_id: Optional[str] = None, session_id: str = None) -> Optional[TestVariant]:
        """Get appropriate variant for user/session"""
        
        try:
            test = self.tests.get(test_id)
            if not test or test.status != TestStatus.RUNNING:
                return None
            
            # Use user_id if available, otherwise session_id
            identifier = user_id or session_id
            if not identifier:
                return None
            
            # Check existing assignment
            assignments = self.user_assignments if user_id else self.session_assignments
            
            if identifier in assignments and test_id in assignments[identifier]:
                variant_id = assignments[identifier][test_id]
                
                # Find variant
                for variant in test.variants:
                    if variant.variant_id == variant_id and variant.is_active:
                        return variant
            
            # New assignment needed
            active_variants = [v for v in test.variants if v.is_active]
            if not active_variants:
                return None
            
            # Use deterministic assignment based on identifier
            hash_input = f"{test_id}:{identifier}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
            hash_ratio = (hash_value % 10000) / 10000.0
            
            # Assign based on traffic allocation
            cumulative_allocation = 0.0
            selected_variant = None
            
            for variant in active_variants:
                cumulative_allocation += variant.traffic_allocation
                if hash_ratio <= cumulative_allocation:
                    selected_variant = variant
                    break
            
            # Store assignment
            if selected_variant:
                if identifier not in assignments:
                    assignments[identifier] = {}
                assignments[identifier][test_id] = selected_variant.variant_id
                
                logger.info(f"🧪 Assigned {identifier} to variant {selected_variant.name} in test {test.name}")
            
            return selected_variant
            
        except Exception as e:
            logger.error(f"Variant assignment failed: {str(e)}")
            return None
    
    def track_event(self, test_id: str, event_type: str, event_data: Dict[str, Any], 
                   user_id: Optional[str] = None, session_id: str = None) -> bool:
        """Track A/B test event"""
        
        try:
            test = self.tests.get(test_id)
            if not test:
                return False
            
            identifier = user_id or session_id
            if not identifier:
                return False
            
            # Get user's variant
            variant = self.get_variant_for_user(test_id, user_id, session_id)
            if not variant:
                return False
            
            # Create event
            event = TestEvent(
                event_id=str(uuid.uuid4()),
                test_id=test_id,
                variant_id=variant.variant_id,
                user_id=user_id,
                session_id=session_id or "",
                event_type=event_type,
                event_data=event_data,
                timestamp=datetime.now()
            )
            
            # Store event
            if test_id not in self.events:
                self.events[test_id] = []
            
            self.events[test_id].append(event)
            
            logger.info(f"🧪 Tracked event {event_type} for test {test.name}, variant {variant.name}")
            return True
            
        except Exception as e:
            logger.error(f"Event tracking failed: {str(e)}")
            return False
    
    def calculate_test_results(self, test_id: str) -> Optional[TestResults]:
        """Calculate statistical results for A/B test"""
        
        try:
            test = self.tests.get(test_id)
            if not test:
                return None
            
            events = self.events.get(test_id, [])
            if not events:
                return None
            
            # Group events by variant
            variant_events = {}
            for variant in test.variants:
                variant_events[variant.variant_id] = [e for e in events if e.variant_id == variant.variant_id]
            
            # Calculate metrics for each variant
            variant_results = {}
            
            for variant in test.variants:
                variant_id = variant.variant_id
                events_list = variant_events.get(variant_id, [])
                
                # Calculate basic metrics
                page_views = len([e for e in events_list if e.event_type == "page_view"])
                conversions = len([e for e in events_list if e.event_type == "conversion"])
                clicks = len([e for e in events_list if e.event_type == "click"])
                
                conversion_rate = conversions / page_views if page_views > 0 else 0
                click_rate = clicks / page_views if page_views > 0 else 0
                
                variant_results[variant_id] = {
                    "variant_name": variant.name,
                    "page_views": page_views,
                    "conversions": conversions,
                    "clicks": clicks,
                    "conversion_rate": conversion_rate,
                    "click_through_rate": click_rate,
                    "total_events": len(events_list)
                }
            
            # Simple statistical significance test (Chi-square test for conversion rates)
            statistical_significance = {}
            confidence_intervals = {}
            
            if len(variant_results) >= 2:
                # Compare each variant to control
                control_variant = next((v for v in test.variants if v.variant_type == VariantType.CONTROL), None)
                
                if control_variant and control_variant.variant_id in variant_results:
                    control_data = variant_results[control_variant.variant_id]
                    
                    for variant_id, data in variant_results.items():
                        if variant_id != control_variant.variant_id:
                            # Simple significance test (placeholder - use proper statistical library in production)
                            significance = self._calculate_significance(control_data, data)
                            statistical_significance[variant_id] = significance
                            
                            # Calculate confidence intervals
                            ci = self._calculate_confidence_interval(data["conversion_rate"], data["page_views"])
                            confidence_intervals[variant_id] = ci
            
            # Generate recommendations
            recommendations = self._generate_recommendations(test, variant_results, statistical_significance)
            
            # Determine winner
            winner_variant = self._determine_winner(variant_results, statistical_significance)
            
            return TestResults(
                test_id=test_id,
                variant_results=variant_results,
                statistical_significance=statistical_significance,
                confidence_intervals=confidence_intervals,
                recommendations=recommendations,
                winner_variant=winner_variant
            )
            
        except Exception as e:
            logger.error(f"Results calculation failed: {str(e)}")
            return None
    
    def _calculate_significance(self, control_data: Dict, variant_data: Dict) -> bool:
        """Simple significance calculation (placeholder)"""
        
        # This is a simplified version - use proper statistical libraries in production
        control_rate = control_data["conversion_rate"]
        variant_rate = variant_data["conversion_rate"]
        control_views = control_data["page_views"]
        variant_views = variant_data["page_views"]
        
        # Need minimum sample size
        if control_views < 30 or variant_views < 30:
            return False
        
        # Simple difference threshold (placeholder)
        rate_difference = abs(variant_rate - control_rate)
        return rate_difference > 0.02 and min(control_views, variant_views) > 100
    
    def _calculate_confidence_interval(self, conversion_rate: float, sample_size: int) -> Dict[str, float]:
        """Calculate confidence interval for conversion rate"""
        
        if sample_size == 0:
            return {"lower": 0.0, "upper": 0.0}
        
        # Simple approximation (use proper statistical methods in production)
        import math
        
        z_score = 1.96  # 95% confidence
        se = math.sqrt((conversion_rate * (1 - conversion_rate)) / sample_size)
        margin = z_score * se
        
        return {
            "lower": max(0.0, conversion_rate - margin),
            "upper": min(1.0, conversion_rate + margin)
        }
    
    def _generate_recommendations(self, test: ABTest, variant_results: Dict, significance: Dict) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Check if test has enough data
        total_views = sum([data["page_views"] for data in variant_results.values()])
        
        if total_views < 100:
            recommendations.append("🔍 Test benötigt mehr Daten für statistisch signifikante Ergebnisse")
        
        # Find best performing variant
        best_variant = max(variant_results.items(), key=lambda x: x[1]["conversion_rate"])
        best_id, best_data = best_variant
        
        if best_data["conversion_rate"] > 0:
            variant_name = best_data["variant_name"]
            recommendations.append(f"🏆 Variant '{variant_name}' zeigt beste Performance ({best_data['conversion_rate']:.2%} Conversion Rate)")
        
        # Check for significant differences
        significant_variants = [vid for vid, is_sig in significance.items() if is_sig]
        
        if significant_variants:
            recommendations.append(f"📊 {len(significant_variants)} Varianten zeigen statistisch signifikante Unterschiede")
        else:
            recommendations.append("⚖️ Noch keine statistisch signifikanten Unterschiede erkennbar")
        
        # Performance insights
        avg_conversion = sum([data["conversion_rate"] for data in variant_results.values()]) / len(variant_results)
        
        if avg_conversion < 0.02:
            recommendations.append("⚠️ Niedrige Conversion Rate - Überprüfung der Zielgruppe oder Angebots empfohlen")
        elif avg_conversion > 0.10:
            recommendations.append("✅ Hohe Conversion Rate - Test zeigt gute Performance")
        
        return recommendations
    
    def _determine_winner(self, variant_results: Dict, significance: Dict) -> Optional[str]:
        """Determine winning variant based on results"""
        
        # Find variant with highest conversion rate that's also significant
        best_variant = None
        best_rate = 0
        
        for variant_id, data in variant_results.items():
            if data["conversion_rate"] > best_rate:
                # Check if significant or if it's the only variant with data
                if variant_id in significance and significance[variant_id]:
                    best_variant = variant_id
                    best_rate = data["conversion_rate"]
                elif len(variant_results) == 1 or data["page_views"] > 200:
                    best_variant = variant_id
                    best_rate = data["conversion_rate"]
        
        return best_variant
    
    # ========== TEST MANAGEMENT ==========
    
    def create_test(self, test_data: Dict[str, Any]) -> str:
        """Create new A/B test"""
        
        try:
            test_id = str(uuid.uuid4())
            
            # Create variants
            variants = []
            for i, variant_data in enumerate(test_data.get("variants", [])):
                variant = TestVariant(
                    variant_id=str(uuid.uuid4()),
                    name=variant_data["name"],
                    variant_type=VariantType(variant_data.get("type", "variant")),
                    traffic_allocation=variant_data.get("traffic_allocation", 1.0 / len(test_data["variants"])),
                    configuration=variant_data.get("configuration", {})
                )
                variants.append(variant)
            
            # Create metrics
            metrics = []
            for metric_data in test_data.get("metrics", []):
                metric = TestMetric(
                    metric_id=str(uuid.uuid4()),
                    name=metric_data["name"],
                    metric_type=MetricType(metric_data["type"]),
                    goal_value=metric_data.get("goal_value"),
                    is_primary=metric_data.get("is_primary", False),
                    description=metric_data.get("description")
                )
                metrics.append(metric)
            
            # Create test
            test = ABTest(
                test_id=test_id,
                name=test_data["name"],
                description=test_data.get("description", ""),
                page_path=test_data["page_path"],
                status=TestStatus(test_data.get("status", "draft")),
                variants=variants,
                metrics=metrics,
                sample_size_target=test_data.get("sample_size_target"),
                confidence_level=test_data.get("confidence_level", 0.95),
                created_by=test_data.get("created_by", "")
            )
            
            self.tests[test_id] = test
            self.events[test_id] = []
            
            logger.info(f"🧪 A/B test created: {test.name}")
            return test_id
            
        except Exception as e:
            logger.error(f"Test creation failed: {str(e)}")
            raise
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get A/B test by ID"""
        return self.tests.get(test_id)
    
    def list_tests(self, status: Optional[str] = None, page_path: Optional[str] = None) -> List[ABTest]:
        """List A/B tests with optional filters"""
        
        tests = list(self.tests.values())
        
        if status:
            tests = [t for t in tests if t.status.value == status]
        
        if page_path:
            tests = [t for t in tests if t.page_path == page_path]
        
        return tests
    
    def start_test(self, test_id: str) -> bool:
        """Start A/B test"""
        
        try:
            test = self.tests.get(test_id)
            if not test:
                return False
            
            test.status = TestStatus.RUNNING
            test.start_date = datetime.now()
            test.updated_at = datetime.now()
            
            logger.info(f"🧪 A/B test started: {test.name}")
            return True
            
        except Exception as e:
            logger.error(f"Start test failed: {str(e)}")
            return False
    
    def stop_test(self, test_id: str) -> bool:
        """Stop A/B test"""
        
        try:
            test = self.tests.get(test_id)
            if not test:
                return False
            
            test.status = TestStatus.COMPLETED
            test.end_date = datetime.now()
            test.updated_at = datetime.now()
            
            logger.info(f"🧪 A/B test stopped: {test.name}")
            return True
            
        except Exception as e:
            logger.error(f"Stop test failed: {str(e)}")
            return False
    
    def get_active_tests_for_path(self, page_path: str) -> List[ABTest]:
        """Get active tests for specific page path"""
        
        return [
            test for test in self.tests.values()
            if test.status == TestStatus.RUNNING and test.page_path == page_path
        ]
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get overall A/B testing statistics"""
        
        try:
            total_tests = len(self.tests)
            running_tests = len([t for t in self.tests.values() if t.status == TestStatus.RUNNING])
            completed_tests = len([t for t in self.tests.values() if t.status == TestStatus.COMPLETED])
            
            total_events = sum([len(events) for events in self.events.values()])
            total_users = len(self.user_assignments)
            total_sessions = len(self.session_assignments)
            
            # Page coverage
            pages_tested = len(set([test.page_path for test in self.tests.values()]))
            
            return {
                "total_tests": total_tests,
                "running_tests": running_tests,
                "completed_tests": completed_tests,
                "total_events": total_events,
                "total_users_tested": total_users,
                "total_sessions": total_sessions,
                "pages_with_tests": pages_tested,
                "test_coverage": {
                    "homepage": len([t for t in self.tests.values() if t.page_path == "/"]),
                    "pricing": len([t for t in self.tests.values() if t.page_path == "/pricing"]),
                    "signup": len([t for t in self.tests.values() if t.page_path == "/signup"])
                }
            }
            
        except Exception as e:
            logger.error(f"Statistics calculation failed: {str(e)}")
            return {}

# Global A/B testing manager
ab_testing_manager = ABTestingManager()