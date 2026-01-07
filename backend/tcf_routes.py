"""
TCF 2.2 API Routes
API Endpoints für IAB Transparency & Consent Framework Daten
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from database_service import db_service
from compliance_engine.tcf_vendor_analyzer import tcf_vendor_analyzer

router = APIRouter(prefix="/api/tcf", tags=["TCF 2.2"])
security = HTTPBearer()


# Response Models
class TCFStatusResponse(BaseModel):
    scan_id: str
    url: str
    has_tcf: bool
    tcf_version: Optional[str]
    cmp_name: Optional[str]
    cmp_id: Optional[int]
    tc_string_found: bool
    vendor_count: int
    scanned_at: datetime


class VendorInfo(BaseModel):
    vendor_id: str
    vendor_name: str
    detected_from: str
    requires_consent: bool
    purposes: List[Dict[str, Any]] = []


class VendorsResponse(BaseModel):
    scan_id: str
    total_vendors: int
    vendors: List[VendorInfo]


class TCStringDetails(BaseModel):
    scan_id: str
    tc_string_present: bool
    tc_string_valid: Optional[bool]
    version: Optional[str]
    segments_count: Optional[int]
    parsed_data: Optional[Dict[str, Any]]


class TCFComplianceReport(BaseModel):
    scan_id: str
    url: str
    has_tcf: bool
    compliance_status: str  # "compliant", "partial", "non_compliant", "not_applicable"
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    vendor_summary: Dict[str, Any]


# Helper: Get Current User from Token
async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user ID from JWT token"""
    try:
        from auth_routes import get_current_user
        user = await get_current_user(credentials)
        return user["user_id"]
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")


# ==================== TCF ENDPOINTS ====================

@router.get("/status/{scan_id}", response_model=TCFStatusResponse)
async def get_tcf_status(
    scan_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Holt TCF Status für einen Scan
    """
    
    # Lade Scan aus Datenbank
    query = """
        SELECT 
            id, url, scan_results, scanned_at
        FROM analysis_results
        WHERE id = $1 AND user_id = $2
    """
    
    scan = await db_service.pool.fetchrow(query, scan_id, user_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    # Extrahiere TCF Daten aus scan_results
    scan_results = scan['scan_results']
    tcf_data = scan_results.get('tcf_data', {})
    
    return TCFStatusResponse(
        scan_id=str(scan['id']),
        url=scan['url'],
        has_tcf=tcf_data.get('has_tcf', False),
        tcf_version=tcf_data.get('tcf_version'),
        cmp_name=tcf_data.get('cmp_name'),
        cmp_id=tcf_data.get('cmp_id'),
        tc_string_found=tcf_data.get('tc_string_found', False),
        vendor_count=tcf_data.get('vendor_count', 0),
        scanned_at=scan['scanned_at']
    )


@router.get("/vendors/{scan_id}", response_model=VendorsResponse)
async def get_tcf_vendors(
    scan_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Liste aller erkannten TCF Vendors für einen Scan
    """
    
    # Lade Scan aus Datenbank
    query = """
        SELECT 
            id, scan_results
        FROM analysis_results
        WHERE id = $1 AND user_id = $2
    """
    
    scan = await db_service.pool.fetchrow(query, scan_id, user_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    # Extrahiere Vendor Daten
    scan_results = scan['scan_results']
    tcf_data = scan_results.get('tcf_data', {})
    detected_vendors = tcf_data.get('detected_vendors', [])
    
    # Lade GVL für zusätzliche Vendor-Infos
    await tcf_vendor_analyzer.load_global_vendor_list()
    
    # Enriche Vendors mit Purposes
    enriched_vendors = []
    for vendor in detected_vendors:
        vendor_id = int(vendor['vendor_id'])
        purposes = tcf_vendor_analyzer.get_vendor_purposes(vendor_id)
        
        enriched_vendors.append(VendorInfo(
            vendor_id=vendor['vendor_id'],
            vendor_name=vendor['vendor_name'],
            detected_from=vendor.get('detected_from', 'unknown'),
            requires_consent=vendor.get('requires_consent', True),
            purposes=purposes
        ))
    
    return VendorsResponse(
        scan_id=str(scan['id']),
        total_vendors=len(enriched_vendors),
        vendors=enriched_vendors
    )


@router.get("/consent-string/{scan_id}", response_model=TCStringDetails)
async def get_tc_string_details(
    scan_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Parsed TC String Details (wenn verfügbar)
    """
    
    # Lade Scan aus Datenbank
    query = """
        SELECT 
            id, scan_results
        FROM analysis_results
        WHERE id = $1 AND user_id = $2
    """
    
    scan = await db_service.pool.fetchrow(query, scan_id, user_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    # Extrahiere TC String Daten
    scan_results = scan['scan_results']
    tcf_data = scan_results.get('tcf_data', {})
    
    tc_string_present = tcf_data.get('tc_string_found', False)
    
    # Parse TC String (wenn vorhanden)
    parsed_data = None
    if tc_string_present and tcf_data.get('tc_string'):
        parsed_data = tcf_vendor_analyzer.parse_tc_string_basic(tcf_data['tc_string'])
    
    return TCStringDetails(
        scan_id=str(scan['id']),
        tc_string_present=tc_string_present,
        tc_string_valid=parsed_data.get('valid') if parsed_data else None,
        version=parsed_data.get('version') if parsed_data else None,
        segments_count=parsed_data.get('segments_count') if parsed_data else None,
        parsed_data=parsed_data
    )


@router.get("/compliance/{scan_id}", response_model=TCFComplianceReport)
async def get_tcf_compliance_report(
    scan_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Vollständiger TCF Compliance Report
    """
    
    # Lade Scan aus Datenbank
    query = """
        SELECT 
            id, url, scan_results
        FROM analysis_results
        WHERE id = $1 AND user_id = $2
    """
    
    scan = await db_service.pool.fetchrow(query, scan_id, user_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    # Extrahiere TCF Daten
    scan_results = scan['scan_results']
    tcf_data = scan_results.get('tcf_data', {})
    
    has_tcf = tcf_data.get('has_tcf', False)
    
    # Bestimme Compliance Status
    if not has_tcf:
        compliance_status = "not_applicable"
        recommendations = [
            "TCF 2.2 ist optional. Empfohlen für Publisher mit programmatic advertising."
        ]
    elif tcf_data.get('tc_string_found') and len(tcf_data.get('issues', [])) == 0:
        compliance_status = "compliant"
        recommendations = [
            "✅ TCF 2.2 ist korrekt implementiert",
            "Stellen Sie sicher, dass alle Vendors in der GVL registriert sind"
        ]
    elif tcf_data.get('tc_string_found'):
        compliance_status = "partial"
        recommendations = [
            "TCF ist vorhanden, aber mit Problemen",
            "Prüfen Sie die Issues unten für Details"
        ]
    else:
        compliance_status = "non_compliant"
        recommendations = [
            "⚠️ TCF API gefunden, aber TC String fehlt",
            "Prüfen Sie Ihre CMP-Konfiguration"
        ]
    
    # Vendor Summary
    detected_vendors = tcf_data.get('detected_vendors', [])
    vendor_summary = {
        "total_vendors": len(detected_vendors),
        "vendors_requiring_consent": len([v for v in detected_vendors if v.get('requires_consent')]),
        "top_vendors": [v['vendor_name'] for v in detected_vendors[:5]]
    }
    
    return TCFComplianceReport(
        scan_id=str(scan['id']),
        url=scan['url'],
        has_tcf=has_tcf,
        compliance_status=compliance_status,
        issues=tcf_data.get('issues', []),
        recommendations=recommendations,
        vendor_summary=vendor_summary
    )


# ==================== UTILITY ENDPOINTS ====================

@router.get("/gvl/vendors")
async def get_global_vendor_list(
    limit: int = 100,
    offset: int = 0
):
    """
    Holt Global Vendor List (GVL) Vendors
    Öffentlich zugänglich (kein Auth erforderlich)
    """
    
    await tcf_vendor_analyzer.load_global_vendor_list()
    
    if not tcf_vendor_analyzer.gvl_data:
        raise HTTPException(status_code=503, detail="Global Vendor List nicht verfügbar")
    
    vendors = tcf_vendor_analyzer.gvl_data.get('vendors', {})
    
    # Paginierung
    vendor_list = []
    for vendor_id, vendor_data in list(vendors.items())[offset:offset+limit]:
        vendor_list.append({
            "id": vendor_id,
            "name": vendor_data.get('name'),
            "purposes": vendor_data.get('purposes', []),
            "legIntPurposes": vendor_data.get('legIntPurposes', []),
            "specialPurposes": vendor_data.get('specialPurposes', [])
        })
    
    return {
        "total": len(vendors),
        "offset": offset,
        "limit": limit,
        "vendors": vendor_list
    }


@router.get("/gvl/purposes")
async def get_tcf_purposes():
    """
    Holt alle TCF Purposes
    Öffentlich zugänglich
    """
    
    await tcf_vendor_analyzer.load_global_vendor_list()
    
    if not tcf_vendor_analyzer.gvl_data:
        raise HTTPException(status_code=503, detail="Global Vendor List nicht verfügbar")
    
    purposes = tcf_vendor_analyzer.gvl_data.get('purposes', {})
    
    return {
        "total": len(purposes),
        "purposes": [
            {
                "id": purpose_id,
                "name": purpose_data.get('name'),
                "description": purpose_data.get('description', '')
            }
            for purpose_id, purpose_data in purposes.items()
        ]
    }

