import csv, io, json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from app.pipeline import BASE, DB
from app.analytics import query, metadata, NAMES

app = FastAPI(title="Retail Lens", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(BASE / "static/index.html")


@app.get("/health")
def health():
    return {"status": "ok", "warehouse_ready": DB.exists()}


@app.get("/api/meta")
def meta():
    try:
        return metadata()
    except ValueError as e:
        raise HTTPException(503, str(e))


@app.get("/api/quality")
def quality():
    p = BASE / "artifacts/quality.json"
    if not p.exists():
        raise HTTPException(503, "Run bootstrap first.")
    return json.loads(p.read_text())


@app.get("/api/report/{name}")
def report(name: str, start: str, end: str, country: str = "All"):
    try:
        return {"rows": query(name, start, end, country), "currency": "GBP"}
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/api/export/{name}")
def export(name: str, start: str, end: str, country: str = "All"):
    rows = report(name, start, end, country)["rows"]
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=rows[0].keys())
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    k: (
                        "'" + v
                        if isinstance(v, str) and v.startswith(("=", "+", "-", "@"))
                        else v
                    )
                    for k, v in r.items()
                }
            )
    return Response(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={name}.csv"},
    )


@app.get("/api/sql/{name}")
def sql(name: str):
    if name not in NAMES:
        raise HTTPException(404, "Unknown report.")
    return {
        "sql": (BASE / "sql" / f"{name}.sql").read_text(),
        "note": "Executed against a date/country-filtered CTE with bound parameters. Cohort acquisition uses full warehouse history.",
    }
