"""
Legal Document Routes — AUDIT-19: DPA Generator (Auftragsverarbeitungsvertrag)
POST /api/v2/legal/generate-dpa
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from jinja2 import Environment, select_autoescape
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

legal_document_router = APIRouter(prefix="/api/v2/legal", tags=["legal-documents"])
security = HTTPBearer()

db_pool = None
auth_service = None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    if auth_service is None:
        raise HTTPException(status_code=503, detail="Auth service not available")
    try:
        user = await auth_service.verify_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# =============================================================================
# AUDIT-19: DPA Generator (Auftragsverarbeitungsvertrag gem. DSGVO Art. 28)
# =============================================================================

class DpaRequest(BaseModel):
    controller_name: str = Field(..., min_length=2, max_length=200)
    controller_address: str = Field(..., min_length=5, max_length=500)
    controller_contact: str = Field(..., min_length=5, max_length=200)
    processor_name: str = Field(..., min_length=2, max_length=200)
    processor_address: str = Field(..., min_length=5, max_length=500)
    processor_contact: str = Field(..., min_length=5, max_length=200)
    processing_purposes: str = Field(..., min_length=10, max_length=1000)
    data_categories: str = Field(..., min_length=5, max_length=500)
    data_subjects: str = Field(..., min_length=5, max_length=300)
    processing_duration: Optional[str] = Field("Bis zur Kündigung des Hauptvertrags", max_length=200)
    subprocessors: Optional[str] = Field("", max_length=1000)
    date: Optional[str] = None


class DpaResponse(BaseModel):
    html: str
    filename: str
    generated_at: str


_dpa_jinja_env = Environment(autoescape=select_autoescape(['html']))

DPA_TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Auftragsverarbeitungsvertrag</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 860px; margin: 2rem auto; line-height: 1.7; padding: 0 1.5rem; color: #222; }
    h1 { font-size: 1.5rem; border-bottom: 2px solid #333; padding-bottom: 0.5rem; }
    h2 { font-size: 1.15rem; margin-top: 2rem; }
    .parties { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; background: #f9f9f9; padding: 1rem; border-radius: 6px; margin: 1rem 0; }
    .party h3 { font-size: 0.95rem; text-transform: uppercase; color: #555; margin: 0 0 0.5rem; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    td, th { border: 1px solid #ccc; padding: 0.6rem 1rem; font-size: 0.9rem; }
    th { background: #f0f0f0; text-align: left; width: 35%; }
    .footer { margin-top: 3rem; border-top: 1px solid #ccc; padding-top: 1.5rem; }
    .sig-block { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; margin-top: 2rem; }
    .sig-line { border-top: 1px solid #333; margin-top: 3rem; padding-top: 0.4rem; font-size: 0.85rem; color: #555; }
    @media print { body { margin: 1cm; } }
  </style>
</head>
<body>
  <h1>Auftragsverarbeitungsvertrag<br><small style="font-weight:normal;font-size:0.9rem;">gemäß Art. 28 DSGVO</small></h1>

  <div class="parties">
    <div class="party">
      <h3>Auftraggeber (Verantwortlicher)</h3>
      <strong>{{ controller_name }}</strong><br>
      {{ controller_address | replace('\n', '<br>') }}<br>
      {{ controller_contact }}
    </div>
    <div class="party">
      <h3>Auftragnehmer (Auftragsverarbeiter)</h3>
      <strong>{{ processor_name }}</strong><br>
      {{ processor_address | replace('\n', '<br>') }}<br>
      {{ processor_contact }}
    </div>
  </div>

  <h2>§ 1 Gegenstand und Dauer der Verarbeitung</h2>
  <table>
    <tr><th>Zweck der Verarbeitung</th><td>{{ processing_purposes }}</td></tr>
    <tr><th>Kategorien betroffener Personen</th><td>{{ data_subjects }}</td></tr>
    <tr><th>Art der personenbezogenen Daten</th><td>{{ data_categories }}</td></tr>
    <tr><th>Dauer der Verarbeitung</th><td>{{ processing_duration }}</td></tr>
  </table>

  <h2>§ 2 Weisungsbefugnis</h2>
  <p>Der Auftragnehmer verarbeitet personenbezogene Daten ausschließlich auf dokumentierte Weisung des Auftraggebers, einschließlich in Bezug auf Übermittlungen personenbezogener Daten an ein Drittland oder eine internationale Organisation.</p>

  <h2>§ 3 Technische und organisatorische Maßnahmen (TOMs)</h2>
  <p>Der Auftragnehmer trifft alle erforderlichen Maßnahmen gemäß Art. 32 DSGVO (Pseudonymisierung, Verschlüsselung, Zugangskontrolle, Verfügbarkeit, Belastbarkeit, Überprüfungs- und Bewertungsverfahren).</p>

  <h2>§ 4 Unterauftragnehmer</h2>
  {% if subprocessors %}
  <p>Folgende Unterauftragnehmer werden eingesetzt:</p>
  <p>{{ subprocessors }}</p>
  {% else %}
  <p>Es werden keine Unterauftragnehmer eingesetzt. Eine Einbindung bedarf der vorherigen schriftlichen Genehmigung des Auftraggebers.</p>
  {% endif %}

  <h2>§ 5 Pflichten des Auftragnehmers</h2>
  <p>Der Auftragnehmer verpflichtet sich insbesondere zur:</p>
  <ul>
    <li>Verschwiegenheit über die verarbeiteten Daten</li>
    <li>Unterstützung bei der Erfüllung von Betroffenenrechten (Art. 12–22 DSGVO)</li>
    <li>Meldung von Datenschutzverletzungen innerhalb von 72 Stunden (Art. 33 DSGVO)</li>
    <li>Löschung oder Rückgabe aller Daten nach Vertragsende</li>
    <li>Bereitstellung aller erforderlichen Informationen für Datenschutz-Folgenabschätzungen</li>
  </ul>

  <h2>§ 6 Rechte des Auftraggebers</h2>
  <p>Der Auftraggeber hat das Recht, Datenschutzaudits durchzuführen oder durch einen beauftragten Prüfer durchführen zu lassen. Der Auftragnehmer unterstützt Audits in angemessener Weise.</p>

  <h2>§ 7 Haftung</h2>
  <p>Die Haftungsregelungen richten sich nach dem Hauptvertrag sowie den Vorschriften der DSGVO. Jede Partei haftet für die ihr zuzurechnenden Schäden nach Maßgabe der Art. 82 DSGVO.</p>

  <div class="footer">
    <p>Erstellt am: {{ date }}</p>
    <div class="sig-block">
      <div>
        <div class="sig-line">Ort, Datum — Auftraggeber</div>
        <div class="sig-line">{{ controller_name }}</div>
      </div>
      <div>
        <div class="sig-line">Ort, Datum — Auftragnehmer</div>
        <div class="sig-line">{{ processor_name }}</div>
      </div>
    </div>
  </div>
</body>
</html>"""


@legal_document_router.post("/generate-dpa", response_model=DpaResponse)
async def generate_dpa(
    request: DpaRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> DpaResponse:
    """AUDIT-19: Generiert einen Auftragsverarbeitungsvertrag (AV-Vertrag) gem. DSGVO Art. 28 als HTML."""
    try:
        template = _dpa_jinja_env.from_string(DPA_TEMPLATE_HTML)
        doc_date = request.date or datetime.now().strftime("%d.%m.%Y")
        html_out = template.render(
            controller_name=request.controller_name,
            controller_address=request.controller_address,
            controller_contact=request.controller_contact,
            processor_name=request.processor_name,
            processor_address=request.processor_address,
            processor_contact=request.processor_contact,
            processing_purposes=request.processing_purposes,
            data_categories=request.data_categories,
            data_subjects=request.data_subjects,
            processing_duration=request.processing_duration,
            subprocessors=request.subprocessors or "",
            date=doc_date,
        )
        filename = f"av-vertrag-{doc_date.replace('.', '-')}.html"
        return DpaResponse(
            html=html_out,
            filename=filename,
            generated_at=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"DPA generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def init_routes(pool, auth_svc):
    global db_pool, auth_service
    db_pool = pool
    auth_service = auth_svc
    logger.info("Legal document routes initialized")
