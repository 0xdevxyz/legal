            "warning": {"min": 500, "max": 2000},
            "pass": {"min": 0, "max": 0}
        },
        "Basis-Barrierefreiheit": {
            "fail": {"min": 500, "max": 2000},
            "warning": {"min": 100, "max": 500},
            "pass": {"min": 0, "max": 0}
        }
    }
    
    total_min = 0
    total_max = 0
    
    for result in results:
        category = result.get("category")
        status = result.get("status")
        
        if category in risk_amounts and status in risk_amounts[category]:
            total_min += risk_amounts[category][status]["min"]
            total_max += risk_amounts[category][status]["max"]
    
    return {"min": total_min, "max": total_max}

def generate_recommendations(results):
    """Spezifische Empfehlungen basierend auf Problemen generieren"""
    recommendations = []
    
    for result in results:
        category = result.get("category")
        status = result.get("status")
        
        if status == "fail":
            if category == "Impressum":
                recommendations.append({
                    "priority": "Hoch",
                    "title": "Impressum erstellen",
                    "description": "Ein rechtsgültiges Impressum nach §5 TMG ist verpflichtend. "
                                  "Fügen Sie alle erforderlichen Angaben hinzu: Name, Anschrift, Kontaktdaten, "
                                  "Vertretungsberechtigte, Registernummer und -gericht, Umsatzsteuer-ID.",
                    "action": "Compliance-Fix aktivieren oder Experten-Service nutzen"
                })
            elif category == "Datenschutzerklärung":
                recommendations.append({
                    "priority": "Hoch",
                    "title": "Datenschutzerklärung implementieren",
                    "description": "Eine DSGVO-konforme Datenschutzerklärung ist gesetzlich vorgeschrieben. "
                                  "Diese muss alle Informationen über Datenerhebung, -verarbeitung, Cookies, "
                                  "Tracking-Tools und Betroffenenrechte enthalten.",
                    "action": "Datenschutzerklärung über Compliance-Fix erstellen lassen"
                })
            elif category == "Cookie-Compliance":
                recommendations.append({
                    "priority": "Hoch",
                    "title": "Cookie-Banner implementieren",
                    "description": "Nach DSGVO und ePrivacy-Richtlinie benötigen Sie ein Cookie-Consent-Banner "
                                  "mit Opt-In für alle nicht-essentiellen Cookies. Dokumentieren Sie alle "
                                  "verwendeten Cookies und deren Zweck.",
                    "action": "Cookie-Consent-System installieren"
                })
            elif category == "Basis-Barrierefreiheit":
                recommendations.append({
                    "priority": "Mittel",
                    "title": "Barrierefreiheit verbessern",
                    "description": "Ihre Website hat grundlegende Probleme mit der Barrierefreiheit. "
                                  "Achten Sie auf Alt-Texte für Bilder, ausreichende Farbkontraste und "
                                  "korrekte Heading-Struktur.",
                    "action": "Barrierefreiheits-Scan durchführen und Anpassungen vornehmen"
                })
        
        elif status == "warning":
            if category == "Cookie-Compliance":
                recommendations.append({
                    "priority": "Mittel",
                    "title": "Cookie-Banner optimieren",
                    "description": "Ihr Cookie-Banner entspricht nicht vollständig den aktuellen Anforderungen. "
                                  "Stellen Sie sicher, dass ein klares Opt-In für Marketing/Analyse-Cookies "
                                  "vorhanden ist und alle Cookies kategorisiert werden.",
                    "action": "Cookie-Banner aktualisieren"
                })
    
    # Allgemeine Empfehlungen hinzufügen, wenn Liste leer ist
    if not recommendations:
        recommendations.append({
            "priority": "Information",
            "title": "Regelmäßige Compliance-Checks",
            "description": "Auch wenn aktuell keine kritischen Probleme vorliegen, empfehlen wir "
                          "monatliche Compliance-Checks, da sich Rechtslage und Website-Inhalte ändern können.",
            "action": "Monatliches Monitoring aktivieren"
        })
    
    return recommendations

async def generate_pdf_report(scan_data, user_info, include_details=True, language="de"):
    """PDF-Bericht aus Scan-Daten generieren"""
    # Berichtsverzeichnis erstellen, falls nicht vorhanden
    report_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    # Dateinamen und Pfad erstellen
    filename = create_report_filename(user_info["id"], scan_data["url"])
    file_path = os.path.join(report_dir, filename)
    
    # Finanzielles Risiko berechnen
    risk = risk_calculator(scan_data["results"])
    
    # Empfehlungen generieren
    recommendations = generate_recommendations(scan_data["results"])
    
    # Template-Daten vorbereiten
    template_data = {
        "scan": scan_data,
        "user": user_info,
        "risk": risk,
        "recommendations": recommendations,
        "include_details": include_details,
        "date": datetime.now().strftime("%d.%m.%Y"),
        "report_id": str(uuid.uuid4())[:8]
    }
    
    # Template basierend auf Sprache auswählen
    template_name = f"report_template_{language}.html"
    template = template_env.get_template(template_name)
    
    # HTML rendern
    html_content = template.render(**template_data)
    
    # PDF generieren
    options = {
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'encoding': 'UTF-8',
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
        'no-outline': None,
        'enable-local-file-access': None
    }
    
    pdfkit.from_string(html_content, file_path, options=options)
    
    # Bericht in Datenbank speichern
    query = """
    INSERT INTO reports (id, user_id, scan_id, file_path, created_at)
    VALUES (:id, :user_id, :scan_id, :file_path, :created_at)
    RETURNING id
    """
    values = {
        "id": str(uuid.uuid4()),
        "user_id": user_info["id"],
        "scan_id": scan_data["id"],
        "file_path": file_path,
        "created_at": datetime.now()
    }
    
    await database.execute(query=query, values=values)
    
    return file_path

@router.post("/generate", response_model=Report)
async def create_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_active_user)
):
    """Einen PDF-Bericht aus einem Scan-Ergebnis generieren"""
    # Scan-Ergebnis abrufen
    scan_data = await get_scan_result(report_request.scan_id, current_user["id"])
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan nicht gefunden")
    
    # Berichts-ID generieren
    report_id = str(uuid.uuid4())
    
    # Prüfen, ob Benutzer Berechtigung basierend auf Abonnement hat
    subscription_tier = current_user["subscription_tier"]
    if subscription_tier == "free" and await get_user_report_count(current_user["id"]) >= 1:
        raise HTTPException(
            status_code=403, 
            detail="Kostenlose Stufe auf 1 Bericht beschränkt. Bitte upgraden Sie, um mehr Berichte zu generieren."
        )
    
    # PDF im Hintergrund generieren
    file_path = await generate_pdf_report(
        scan_data, 
        current_user,
        include_details=report_request.include_details,
        language=report_request.language
    )
    
    # Berichtsdatensatz erstellen
    query = """
    INSERT INTO reports (id, user_id, scan_id, file_path, created_at)
    VALUES (:id, :user_id, :scan_id, :file_path, :created_at)
    RETURNING id, user_id, scan_id, file_path, created_at
    """
    values = {
        "id": report_id,
        "user_id": current_user["id"],
        "scan_id": report_request.scan_id,
        "file_path": file_path,
        "created_at": datetime.now()
    }
    
    result = await database.fetch_one(query=query, values=values)
    
    # Berichts-URL erstellen
    base_url = os.environ.get("API_BASE_URL", "https://api.complyo.tech")
    report_url = f"{base_url}/api/reports/download/{report_id}"
    
    return {**dict(result), "url": report_url}

@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    current_user = Depends(get_current_active_user)
):
    """Einen generierten PDF-Bericht herunterladen"""
    # Bericht abrufen
    query = """
    SELECT * FROM reports WHERE id = :report_id AND user_id = :user_id
    """
    values = {"report_id": report_id, "user_id": current_user["id"]}
    report = await database.fetch_one(query=query, values=values)
    
    if not report:
        raise HTTPException(status_code=404, detail="Bericht nicht gefunden")
    
    # Prüfen, ob Datei existiert
    file_path = report["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Berichtsdatei nicht gefunden")
    
    # Dateinamen aus Pfad extrahieren
    filename = os.path.basename(file_path)
    
    # Datei zurückgeben
    return FileResponse(
        path=file_path, 
        filename=filename,
        media_type="application/pdf"
    )

@router.get("/list")
async def list_reports(current_user = Depends(get_current_active_user)):
    """Alle Berichte für den aktuellen Benutzer auflisten"""
    query = """
    SELECT r.id, r.scan_id, r.created_at, s.url 
    FROM reports r
    JOIN scan_results s ON r.scan_id = s.id
    WHERE r.user_id = :user_id
    ORDER BY r.created_at DESC
    """
    values = {"user_id": current_user["id"]}
    reports = await database.fetch_all(query=query, values=values)
    
    # URLs für jeden Bericht generieren
    base_url = os.environ.get("API_BASE_URL", "https://api.complyo.tech")
    result = []
    
    for report in reports:
        report_dict = dict(report)
        report_dict["url"] = f"{base_url}/api/reports/download/{report['id']}"
        result.append(report_dict)
    
    return result

async def get_user_report_count(user_id: str):
    """Die Anzahl der von einem Benutzer generierten Berichte abrufen"""
    query = "SELECT COUNT(*) as count FROM reports WHERE user_id = :user_id"
    values = {"user_id": user_id}
    result = await database.fetch_one(query=query, values=values)
    return result["count"]

# DB-Init-Funktion - rufen Sie diese auf, wenn Ihre App startet
async def init_db():
    # reports-Tabelle erstellen, falls nicht vorhanden
    query = """
    CREATE TABLE IF NOT EXISTS reports (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL REFERENCES users(id),
        scan_id VARCHAR(50) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
    """
    await database.execute(query=query)
    
    # scan_results-Tabelle erstellen, falls nicht vorhanden
    query = """
    CREATE TABLE IF NOT EXISTS scan_results (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL REFERENCES users(id),
        url VARCHAR(255) NOT NULL,
        overall_score INTEGER NOT NULL,
        total_issues INTEGER NOT NULL,
        results TEXT NOT NULL,  -- JSON-String
        scan_timestamp TIMESTAMP NOT NULL,
        scan_duration_ms INTEGER NOT NULL
    )
    """
    await database.execute(query=query)
