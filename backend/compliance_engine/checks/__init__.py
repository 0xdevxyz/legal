"""
Modulare Compliance-Checks
Jeder Check ist ein eigenständiges Modul für bessere Wartbarkeit
"""

from .impressum_check import check_impressum_compliance, check_impressum_compliance_smart
from .datenschutz_check import check_datenschutz_compliance, check_datenschutz_compliance_smart
from .cookie_check import check_cookie_compliance
from .barrierefreiheit_check import (
    check_barrierefreiheit_compliance,
    check_barrierefreiheit_compliance_smart
)

__all__ = [
    'check_impressum_compliance',
    'check_impressum_compliance_smart',
    'check_datenschutz_compliance',
    'check_datenschutz_compliance_smart',
    'check_cookie_compliance',
    'check_barrierefreiheit_compliance',
    'check_barrierefreiheit_compliance_smart'
]

