import pytest
from datetime import datetime
from uuid import uuid4
from app.risk.engine import RiskScoringEngine, BaseSeverityFactor, AttackTypeFactor, ApplicationContextFactor
from app.models.alert import Alert
from app.models.application import Application
from unittest.mock import MagicMock

def test_base_severity():
    class DummyEntity:
        def __init__(self, severity):
            self.severity = severity

    assert BaseSeverityFactor.calculate(DummyEntity("INFO")) == 10
    assert BaseSeverityFactor.calculate(DummyEntity("LOW")) == 25
    assert BaseSeverityFactor.calculate(DummyEntity("MEDIUM")) == 40
    assert BaseSeverityFactor.calculate(DummyEntity("HIGH")) == 65
    assert BaseSeverityFactor.calculate(DummyEntity("CRITICAL")) == 80

def test_risk_boundaries():
    assert RiskScoringEngine.get_risk_level(0) == "LOW"
    assert RiskScoringEngine.get_risk_level(24) == "LOW"
    assert RiskScoringEngine.get_risk_level(25) == "MODERATE"
    assert RiskScoringEngine.get_risk_level(49) == "MODERATE"
    assert RiskScoringEngine.get_risk_level(50) == "HIGH"
    assert RiskScoringEngine.get_risk_level(74) == "HIGH"
    assert RiskScoringEngine.get_risk_level(75) == "CRITICAL"
    assert RiskScoringEngine.get_risk_level(100) == "CRITICAL"

def test_clamping():
    assert RiskScoringEngine._clamp_score(-5) == 0
    assert RiskScoringEngine._clamp_score(0) == 0
    assert RiskScoringEngine._clamp_score(50) == 50
    assert RiskScoringEngine._clamp_score(100) == 100
    assert RiskScoringEngine._clamp_score(150) == 100

def test_attack_type():
    alert = Alert(title="Brute Force Login")
    assert AttackTypeFactor.calculate_for_alert(None, alert) == 7
    
    alert2 = Alert(title="SQL Injection Detected")
    assert AttackTypeFactor.calculate_for_alert(None, alert2) == 10
    
    alert3 = Alert(title="Unknown Attack")
    assert AttackTypeFactor.calculate_for_alert(None, alert3) == 0

def test_application_context():
    app_dev = Application(name="DevApp", environment="DEVELOPMENT")
    assert ApplicationContextFactor.calculate(app_dev) == 0
    
    app_stage = Application(name="StageApp", environment="STAGING")
    assert ApplicationContextFactor.calculate(app_stage) == 2
    
    app_prod = Application(name="ProdApp", environment="PRODUCTION")
    assert ApplicationContextFactor.calculate(app_prod) == 5
