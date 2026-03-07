from datetime import datetime
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

# In-memory NERIS API credential store (per server process)
_neris_creds: dict = {"client_id": None, "client_secret": None, "connected": False, "entity": None}

from analytics import summarize_incidents
from insights.trends import generate_trend_summary
from insights.report import generate_chiefs_report
from insights.grant import generate_grant_narrative
from convert.nfirs_to_neris import convert_nfirs_csv, summarise_conversion
from quality.scorer import score_incidents
from insights.quality import generate_quality_narrative

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def load_incidents(neris_id: str, use_mock: bool, start: str, end: str):
    start_dt = datetime.strptime(start, "%Y-%m-%d") if start else None
    end_dt   = datetime.strptime(end,   "%Y-%m-%d") if end   else None

    if use_mock:
        from mock_data import generate_incidents, DEPT
        incidents = generate_incidents(start=start_dt, end=end_dt)
        dept_name = DEPT["name"]
    else:
        from neris import fetch_incidents, fetch_entity
        incidents = fetch_incidents(neris_id, start=start_dt, end=end_dt)
        entity    = fetch_entity(neris_id)
        dept_name = entity.get("name", neris_id)

    return incidents, dept_name


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
async def index(request: Request):
    from mock_data import generate_incidents, DEPT
    incidents = generate_incidents()
    stats = summarize_incidents(incidents)
    map_points = [
        {"lat": inc["latitude"], "lon": inc["longitude"], "type": inc.get("incident_type", "Other")}
        for inc in incidents
        if inc.get("latitude") and inc.get("longitude")
    ]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "dashboard": {
            "dept_name": DEPT["name"],
            "stats": stats,
            "map_points": map_points,
        }
    })


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    report_type: str  = Form(...),
    neris_id:    str  = Form("MOCK-001"),
    use_mock:    bool = Form(False),
    start:       str  = Form(""),
    end:         str  = Form(""),
    period:      str  = Form(""),
    grant_type:  str  = Form("AFG"),
    grant_request: str = Form(""),
):
    error = None
    result = None

    try:
        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)

        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            stats = summarize_incidents(incidents)
            period_label = period or ("the selected period" if start or end else "the past year")

            if report_type == "trends":
                result = generate_trend_summary(dept_name, stats, period_label)
            elif report_type == "report":
                result = generate_chiefs_report(dept_name, stats, period_label)
            elif report_type == "grant":
                if not grant_request:
                    error = "Please describe what you are requesting for the grant narrative."
                else:
                    result = generate_grant_narrative(
                        dept_name=dept_name,
                        stats=stats,
                        grant_type=grant_type,
                        request_description=grant_request,
                        period=period_label,
                    )
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": result,
        "error": error,
        "form": {
            "report_type": report_type,
            "neris_id": neris_id,
            "use_mock": use_mock,
            "start": start,
            "end": end,
            "period": period,
            "grant_type": grant_type,
            "grant_request": grant_request,
        },
    })


@app.post("/download")
async def download(content: str = Form(...), filename: str = Form("fireinsight-report.md")):
    return PlainTextResponse(
        content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        media_type="text/markdown",
    )


# ── NFIRS → NERIS Converter ─────────────────────────────────────────────────

@app.post("/convert", response_class=HTMLResponse)
async def convert_upload(
    request: Request,
    file: UploadFile = File(...),
):
    error = None
    incidents = None
    summary = None
    warnings = []
    filename = file.filename or "upload.csv"

    try:
        raw_bytes = await file.read()
        # Try common encodings
        csv_text = None
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                csv_text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if csv_text is None:
            raise ValueError("Could not decode file. Please export your NFIRS data as UTF-8 or Latin-1 CSV.")

        incidents, warnings = convert_nfirs_csv(csv_text)

        if not incidents:
            error = "No incidents found in the uploaded file. Check that it is a valid NFIRS Basic Module CSV export."
        else:
            summary = summarise_conversion(incidents)

    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_tab": "convert",
        "convert": {
            "filename": filename,
            "incidents": incidents,
            "summary": summary,
            "warnings": warnings,
            "error": error,
        },
    })


# ── Data Quality Scorer ──────────────────────────────────────────────────────

@app.post("/quality", response_class=HTMLResponse)
async def quality_score(
    request: Request,
    neris_id: str  = Form("MOCK-001"),
    use_mock: bool = Form(False),
    start:    str  = Form(""),
    end:      str  = Form(""),
    narrative: bool = Form(False),
):
    error = None
    report = None
    ai_narrative = None

    try:
        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)

        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            report = score_incidents(incidents)
            if narrative:
                ai_narrative = generate_quality_narrative(dept_name, report)

    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_tab": "quality",
        "quality": {
            "dept_name": dept_name if not error else "",
            "report": report,
            "narrative": ai_narrative,
            "error": error,
        },
    })


# ── Map Data ────────────────────────────────────────────────────────────────

@app.get("/map-data")
async def map_data(
    neris_id: str = "MOCK-001",
    use_mock: str = "true",
    start: str = "",
    end: str = "",
):
    try:
        incidents, dept_name = load_incidents(neris_id, use_mock.lower() == "true", start, end)
        features = []
        for inc in incidents:
            lat = inc.get("latitude") or inc.get("lat")
            lon = inc.get("longitude") or inc.get("lon")
            if not lat or not lon:
                continue
            features.append({
                "lat": float(lat),
                "lon": float(lon),
                "type": inc.get("incident_type") or "Other",
                "id":   inc.get("neris_id_incident") or inc.get("incident_id") or "",
                "time": inc.get("call_create") or "",
                "arrival": inc.get("arrival_time") or "",
            })
        return JSONResponse({"dept": dept_name, "incidents": features})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── EV / Lithium Battery Fire Analysis ───────────────────────────────────────

@app.post("/ev", response_class=HTMLResponse)
async def ev_analysis(
    request:  Request,
    neris_id: str  = Form("MOCK-001"),
    use_mock: bool = Form(False),
    start:    str  = Form(""),
    end:      str  = Form(""),
):
    error     = None
    report    = None
    dept_name = ""

    try:
        from ev.detector import analyze_ev_incidents
        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)
        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            report = analyze_ev_incidents(incidents)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request":    request,
        "active_tab": "ev",
        "ev": {
            "dept_name": dept_name,
            "report":    report,
            "error":     error,
        },
    })


# ── Community Risk Dashboard ──────────────────────────────────────────────────

@app.post("/risk", response_class=HTMLResponse)
async def risk_dashboard(
    request:  Request,
    neris_id: str  = Form("MOCK-001"),
    use_mock: bool = Form(False),
    start:    str  = Form(""),
    end:      str  = Form(""),
):
    error     = None
    summary   = None
    zones     = None
    dept_name = ""

    try:
        from risk.scorer import compute_risk_zones, compute_risk_summary
        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)
        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            zones   = compute_risk_zones(incidents)
            summary = compute_risk_summary(zones)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request":    request,
        "active_tab": "risk",
        "risk": {
            "dept_name": dept_name,
            "summary":   summary,
            "zones":     zones,
            "error":     error,
        },
    })


# ── Peer Benchmark ───────────────────────────────────────────────────────────

@app.post("/benchmark", response_class=HTMLResponse)
async def benchmark(
    request:    Request,
    neris_id:   str  = Form("MOCK-001"),
    use_mock:   bool = Form(False),
    start:      str  = Form(""),
    end:        str  = Form(""),
    state:      str  = Form("VA"),
    dept_type:  str  = Form("combination"),
    population: int  = Form(25000),
    narrative:  bool = Form(False),
):
    error = None
    result = None
    ai_narrative = None
    dept_name = ""

    try:
        from benchmark.engine import run_benchmark
        from insights.benchmark_narrative import generate_benchmark_narrative

        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)

        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            stats  = summarize_incidents(incidents)
            result = run_benchmark(
                dept_stats=stats,
                dept_name=dept_name,
                state=state,
                dept_type=dept_type,
                population=population,
            )
            if narrative:
                ai_narrative = generate_benchmark_narrative(result)

    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_tab": "benchmark",
        "benchmark": {
            "result":    result,
            "narrative": ai_narrative,
            "error":     error,
            "form": {
                "state":      state,
                "dept_type":  dept_type,
                "population": population,
            },
        },
    })


# ── NERIS Compliance Tracker ─────────────────────────────────────────────────

@app.post("/compliance", response_class=HTMLResponse)
async def compliance_check(
    request:  Request,
    neris_id: str  = Form("MOCK-001"),
    use_mock: bool = Form(False),
    start:    str  = Form(""),
    end:      str  = Form(""),
):
    error     = None
    report    = None
    dept_name = ""

    try:
        from compliance.checker import check_compliance
        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)
        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            report = check_compliance(incidents)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request":    request,
        "active_tab": "compliance",
        "compliance": {
            "dept_name": dept_name,
            "report":    report,
            "error":     error,
        },
    })


# ── ISO Evidence Pack ─────────────────────────────────────────────────────────

@app.post("/iso", response_class=HTMLResponse)
async def iso_evidence(
    request:   Request,
    neris_id:  str  = Form("MOCK-001"),
    use_mock:  bool = Form(False),
    start:     str  = Form(""),
    end:       str  = Form(""),
    period:    str  = Form(""),
    narrative: bool = Form(False),
):
    error       = None
    iso_metrics = None
    ai_narrative = None
    dept_name   = ""

    try:
        from insights.iso_narrative import compute_iso_metrics, generate_iso_narrative
        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)
        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            stats       = summarize_incidents(incidents)
            iso_metrics = compute_iso_metrics(incidents)
            period_label = period or ("the selected period" if start or end else "the past year")
            if narrative and iso_metrics:
                ai_narrative = generate_iso_narrative(dept_name, stats, iso_metrics, period_label)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request":    request,
        "active_tab": "iso",
        "iso": {
            "dept_name":   dept_name,
            "iso_metrics": iso_metrics,
            "narrative":   ai_narrative,
            "error":       error,
        },
    })


# ── Staffing Justification Report ────────────────────────────────────────────

@app.post("/staffing", response_class=HTMLResponse)
async def staffing_report(
    request:   Request,
    neris_id:  str  = Form("MOCK-001"),
    use_mock:  bool = Form(False),
    start:     str  = Form(""),
    end:       str  = Form(""),
    narrative: bool = Form(False),
):
    error       = None
    report      = None
    ai_narrative = None
    dept_name   = ""

    try:
        from staffing.analyzer import analyze_staffing
        from insights.staffing_narrative import generate_staffing_narrative
        incidents, dept_name = load_incidents(neris_id, use_mock, start, end)
        if not incidents:
            error = "No incidents found for the given parameters."
        else:
            report = analyze_staffing(incidents)
            if narrative and report:
                ai_narrative = generate_staffing_narrative(dept_name, report)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("index.html", {
        "request":    request,
        "active_tab": "staffing",
        "staffing": {
            "dept_name": dept_name,
            "report":    report,
            "narrative": ai_narrative,
            "error":     error,
        },
    })


# ── NERIS API Connection ──────────────────────────────────────────────────────

@app.post("/neris/connect", response_class=JSONResponse)
async def neris_connect(
    client_id:     str = Form(...),
    client_secret: str = Form(...),
):
    global _neris_creds
    try:
        import httpx
        token_url = "https://auth.neris.fsri.org/oauth2/token"
        resp = httpx.post(token_url, data={
            "grant_type":    "client_credentials",
            "client_id":     client_id,
            "client_secret": client_secret,
        }, timeout=10)
        if resp.status_code == 200:
            _neris_creds = {
                "client_id":     client_id,
                "client_secret": client_secret,
                "connected":     True,
                "entity":        client_id,
            }
            return JSONResponse({"ok": True, "message": "Connected to NERIS API successfully."})
        else:
            _neris_creds["connected"] = False
            return JSONResponse({"ok": False, "message": f"Authentication failed (HTTP {resp.status_code}). Check your Client ID and Secret."}, status_code=400)
    except Exception as e:
        _neris_creds["connected"] = False
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)


@app.get("/neris/status", response_class=JSONResponse)
async def neris_status():
    return JSONResponse({
        "connected": _neris_creds.get("connected", False),
        "entity":    _neris_creds.get("entity"),
    })


# ── Resources / Education ─────────────────────────────────────────────────────

@app.get("/resources", response_class=HTMLResponse)
async def resources_index(request: Request):
    from articles import ARTICLES
    return templates.TemplateResponse("resources.html", {
        "request": request,
        "articles": ARTICLES,
    })


@app.get("/resources/{slug}", response_class=HTMLResponse)
async def resource_article(request: Request, slug: str):
    from articles import get_article, ARTICLES
    article = get_article(slug)
    if not article:
        return HTMLResponse("<h1>Article not found</h1>", status_code=404)
    slugs = [a["slug"] for a in ARTICLES]
    idx = slugs.index(slug)
    prev_article = ARTICLES[idx - 1] if idx > 0 else None
    next_article = ARTICLES[idx + 1] if idx < len(ARTICLES) - 1 else None
    return templates.TemplateResponse("article.html", {
        "request": request,
        "article": article,
        "prev_article": prev_article,
        "next_article": next_article,
    })


@app.post("/convert/download")
async def convert_download(
    content: str = Form(...),
    filename: str = Form("neris-incidents.json"),
):
    return PlainTextResponse(
        content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        media_type="application/json",
    )
