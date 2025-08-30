#!/usr/bin/env python3
"""
Complyo System Compatibility Test
Test script to verify that all components work together without conflicts
"""

import sys
import asyncio
import importlib
from typing import Dict, Any, List

class CompatibilityTester:
    def __init__(self):
        self.test_results = []
        
    def test_module_import(self, module_path: str, description: str) -> bool:
        """Test if a module can be imported without errors"""
        try:
            importlib.import_module(module_path)
            self.test_results.append({
                "test": f"Import {module_path}",
                "description": description,
                "status": "✅ PASS",
                "error": None
            })
            return True
        except Exception as e:
            self.test_results.append({
                "test": f"Import {module_path}",
                "description": description,
                "status": "❌ FAIL",
                "error": str(e)
            })
            return False
    
    def test_existing_system_components(self):
        """Test existing Complyo system components"""
        print("🔍 Testing existing system components...")
        
        # Core existing modules
        existing_modules = [
            ("backend.main", "Main FastAPI application"),
            ("backend.compliance_scanner", "Website compliance scanner"),
            ("backend.ai_compliance_engine", "Existing AI compliance engine"),
            ("backend.website_scanner", "Website content scanner"),
            ("backend.monitoring_system", "24/7 monitoring system"),
            ("backend.email_service", "Email notification service"),
            ("backend.database_models", "Database models and management"),
        ]
        
        for module_path, description in existing_modules:
            self.test_module_import(module_path, f"Existing: {description}")
    
    def test_new_ai_engine_components(self):
        """Test new AI engine components for compatibility"""
        print("🤖 Testing new AI engine components...")
        
        ai_modules = [
            ("backend.ai_engine.compliance_ai", "Enhanced AI compliance analysis"),
            ("backend.ai_engine.trainer", "ML model trainer"),
            ("backend.ai_engine.features", "ML feature extraction engine"),
            ("backend.ai_engine.evaluator", "ML model evaluation system"),
            ("backend.ai_engine.predictor", "Real-time compliance prediction"),
            ("backend.ai_engine.nlp", "NLP text processing engine"),
            ("backend.ai_engine.text_analysis", "Advanced text analysis"),
            ("backend.ai_engine.recommendations", "AI-powered recommendations"),
        ]
        
        for module_path, description in ai_modules:
            self.test_module_import(module_path, f"New AI: {description}")
    
    def test_monitoring_enhancement(self):
        """Test monitoring enhancement module"""
        print("📊 Testing monitoring enhancement...")
        
        self.test_module_import(
            "backend.monitoring.metrics", 
            "Enhanced metrics collection system"
        )
    
    def test_integration_compatibility(self):
        """Test if new modules can work with existing ones"""
        print("🔗 Testing integration compatibility...")
        
        try:
            # Test AI engine integration
            from backend.ai_engine.compliance_ai import compliance_ai
            
            # Simulate compatibility test
            test_data = {"url": "https://example.com", "content": "privacy policy cookie consent"}
            
            # This should work without errors if properly integrated
            result = asyncio.run(compliance_ai.analyze_gdpr_compliance(test_data))
            
            if isinstance(result, dict) and "compliance_score" in result:
                self.test_results.append({
                    "test": "AI Engine Integration",
                    "description": "New AI engine works with existing system",
                    "status": "✅ PASS",
                    "error": None
                })
            else:
                self.test_results.append({
                    "test": "AI Engine Integration",
                    "description": "New AI engine integration test",
                    "status": "❌ FAIL",
                    "error": "Invalid result format"
                })
                
        except Exception as e:
            self.test_results.append({
                "test": "AI Engine Integration",
                "description": "New AI engine integration test",
                "status": "❌ FAIL",
                "error": str(e)
            })
    
    def run_all_tests(self):
        """Run all compatibility tests"""
        print("🚀 Starting Complyo System Compatibility Tests\\n")
        
        self.test_existing_system_components()
        print()
        
        self.test_new_ai_engine_components()
        print()
        
        self.test_monitoring_enhancement()
        print()
        
        self.test_integration_compatibility()
        print()
        
        self.print_results()
    
    def print_results(self):
        """Print test results summary"""
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = 0
        failed = 0
        
        for result in self.test_results:
            status_icon = "✅" if "PASS" in result["status"] else "❌"
            print(f"{status_icon} {result['test']}")
            print(f"   📝 {result['description']}")
            
            if result["error"]:
                print(f"   🐛 Error: {result['error']}")
            
            if "PASS" in result["status"]:
                passed += 1
            else:
                failed += 1
            
            print()
        
        print("=" * 80)
        print(f"📊 SUMMARY: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED - System is fully compatible!")
        else:
            print("⚠️  Some tests failed - Check errors above")
        
        return failed == 0

def main():
    """Main test function"""
    print("Complyo System Compatibility Test")
    print("Testing integration between existing and new components\\n")
    
    # Add backend to Python path
    sys.path.insert(0, '/home/user/webapp')
    
    tester = CompatibilityTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()