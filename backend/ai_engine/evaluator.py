"""Model Performance Evaluation
Evaluates ML model performance and provides metrics
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, mean_squared_error,
    mean_absolute_error, r2_score
)
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

class ModelEvaluator:
    """Comprehensive ML model evaluation and metrics"""
    
    def __init__(self):
        self.evaluation_history = []
        
    def evaluate_classification_model(self, 
                                    y_true: np.ndarray, 
                                    y_pred: np.ndarray,
                                    y_pred_proba: np.ndarray = None,
                                    model_name: str = "Unknown") -> Dict[str, Any]:
        """Evaluate classification model performance"""
        
        metrics = {
            "model_name": model_name,
            "evaluation_date": datetime.utcnow().isoformat(),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, average='weighted', zero_division=0)),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist()
        }
        
        # Add AUC if probabilities are provided
        if y_pred_proba is not None:
            try:
                metrics["auc_roc"] = float(roc_auc_score(y_true, y_pred_proba[:, 1]))
            except:
                metrics["auc_roc"] = None
        
        # Classification report details
        metrics["classification_details"] = self._get_classification_details(y_true, y_pred)
        
        # Store evaluation
        self.evaluation_history.append(metrics)
        
        return metrics
    
    def evaluate_regression_model(self, 
                                y_true: np.ndarray, 
                                y_pred: np.ndarray,
                                model_name: str = "Unknown") -> Dict[str, Any]:
        """Evaluate regression model performance"""
        
        metrics = {
            "model_name": model_name,
            "evaluation_date": datetime.utcnow().isoformat(),
            "mse": float(mean_squared_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2_score": float(r2_score(y_true, y_pred)),
            "mean_residual": float(np.mean(y_true - y_pred)),
            "std_residual": float(np.std(y_true - y_pred))
        }
        
        # Add percentage-based metrics
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-8))) * 100
        metrics["mape"] = float(mape)
        
        self.evaluation_history.append(metrics)
        return metrics
    
    def evaluate_compliance_model(self, 
                                y_true: np.ndarray, 
                                y_pred: np.ndarray,
                                compliance_type: str = "GDPR") -> Dict[str, Any]:
        """Specialized evaluation for compliance models"""
        
        base_metrics = self.evaluate_classification_model(y_true, y_pred, 
                                                        model_name=f"{compliance_type}_Compliance")
        
        # Compliance-specific metrics
        compliance_metrics = {
            "compliance_type": compliance_type,
            "false_positive_rate": self._calculate_false_positive_rate(y_true, y_pred),
            "false_negative_rate": self._calculate_false_negative_rate(y_true, y_pred),
            "compliance_confidence": self._calculate_compliance_confidence(y_true, y_pred),
            "risk_assessment": self._assess_model_risk(y_true, y_pred)
        }
        
        base_metrics.update(compliance_metrics)
        return base_metrics
    
    def compare_models(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple model evaluations"""
        
        comparison = {
            "comparison_date": datetime.utcnow().isoformat(),
            "models_compared": len(evaluations),
            "best_model": None,
            "model_rankings": [],
            "metric_comparison": {}
        }
        
        # Rank models by key metrics
        if evaluations and "accuracy" in evaluations[0]:
            # Classification comparison
            sorted_models = sorted(evaluations, key=lambda x: x.get("accuracy", 0), reverse=True)
            comparison["best_model"] = sorted_models[0]["model_name"]
            
            for i, model in enumerate(sorted_models):
                comparison["model_rankings"].append({
                    "rank": i + 1,
                    "model_name": model["model_name"],
                    "accuracy": model.get("accuracy", 0),
                    "f1_score": model.get("f1_score", 0)
                })
        
        elif evaluations and "r2_score" in evaluations[0]:
            # Regression comparison
            sorted_models = sorted(evaluations, key=lambda x: x.get("r2_score", 0), reverse=True)
            comparison["best_model"] = sorted_models[0]["model_name"]
        
        return comparison
    
    def generate_evaluation_report(self, evaluation: Dict[str, Any]) -> str:
        """Generate human-readable evaluation report"""
        
        model_name = evaluation.get("model_name", "Unknown Model")
        report = [
            f"# Model Evaluation Report: {model_name}",
            f"**Evaluation Date:** {evaluation.get('evaluation_date', 'Unknown')}",
            "",
            "## Performance Metrics"
        ]
        
        if "accuracy" in evaluation:
            # Classification report
            report.extend([
                f"- **Accuracy:** {evaluation['accuracy']:.3f}",
                f"- **Precision:** {evaluation['precision']:.3f}",
                f"- **Recall:** {evaluation['recall']:.3f}",
                f"- **F1 Score:** {evaluation['f1_score']:.3f}",
            ])
            
            if "auc_roc" in evaluation and evaluation["auc_roc"]:
                report.append(f"- **AUC-ROC:** {evaluation['auc_roc']:.3f}")
        
        elif "r2_score" in evaluation:
            # Regression report
            report.extend([
                f"- **R² Score:** {evaluation['r2_score']:.3f}",
                f"- **RMSE:** {evaluation['rmse']:.3f}",
                f"- **MAE:** {evaluation['mae']:.3f}",
                f"- **MAPE:** {evaluation['mape']:.2f}%"
            ])
        
        # Compliance-specific metrics
        if "compliance_type" in evaluation:
            report.extend([
                "",
                "## Compliance Analysis",
                f"- **Compliance Type:** {evaluation['compliance_type']}",
                f"- **False Positive Rate:** {evaluation['false_positive_rate']:.3f}",
                f"- **False Negative Rate:** {evaluation['false_negative_rate']:.3f}",
                f"- **Risk Assessment:** {evaluation['risk_assessment']}"
            ])
        
        return "\n".join(report)
    
    def _get_classification_details(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """Get detailed classification metrics"""
        unique_labels = np.unique(np.concatenate([y_true, y_pred]))
        
        details = {}
        for label in unique_labels:
            label_mask_true = (y_true == label)
            label_mask_pred = (y_pred == label)
            
            tp = np.sum(label_mask_true & label_mask_pred)
            fp = np.sum(~label_mask_true & label_mask_pred)
            fn = np.sum(label_mask_true & ~label_mask_pred)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            details[f"class_{label}"] = {
                "precision": float(precision),
                "recall": float(recall),
                "support": int(np.sum(label_mask_true))
            }
        
        return details
    
    def _calculate_false_positive_rate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate false positive rate"""
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel() if len(np.unique(y_true)) == 2 else (0, 0, 0, 1)
        return fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    def _calculate_false_negative_rate(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate false negative rate"""
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel() if len(np.unique(y_true)) == 2 else (0, 0, 0, 1)
        return fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    def _calculate_compliance_confidence(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate confidence in compliance predictions"""
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        
        # Weighted confidence score
        confidence = (0.4 * accuracy + 0.3 * precision + 0.3 * recall)
        return float(confidence)
    
    def _assess_model_risk(self, y_true: np.ndarray, y_pred: np.ndarray) -> str:
        """Assess risk level of model predictions"""
        fnr = self._calculate_false_negative_rate(y_true, y_pred)
        fpr = self._calculate_false_positive_rate(y_true, y_pred)
        
        if fnr > 0.2 or fpr > 0.3:
            return "High Risk - High false positive/negative rates"
        elif fnr > 0.1 or fpr > 0.15:
            return "Medium Risk - Moderate error rates"
        else:
            return "Low Risk - Acceptable error rates"
    
    def export_evaluation_history(self, filepath: str = None) -> str:
        """Export evaluation history to JSON"""
        if not filepath:
            filepath = f"model_evaluations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.evaluation_history, f, indent=2)
        
        return filepath
    
    def get_model_performance_trend(self, model_name: str) -> List[Dict[str, Any]]:
        """Get performance trend for a specific model"""
        return [eval_data for eval_data in self.evaluation_history 
                if eval_data.get("model_name") == model_name]