"""Risk Engine: proactive, continuously-computed strategic risks.

RiskScore = Likelihood x Impact x Trend x Confidence. Every risk carries a
reason, evidence, forecast, mitigation, priority and owner — never a bare score.
"""
from striops.risk_engine.engine import assess_risks

__all__ = ["assess_risks"]
