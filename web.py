from datetime import datetime
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

from analytics import summarize_incidents
from insights.trends import generate_trend_summary
from insights.report import generate_chiefs_report
from insights.grant import generate_grant_narrative
from convert.nfirs_to_neris import convert_nfirs_csv, summarise_conversion

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
    return templates.TemplateResponse("index.html", {"request": request})


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
