from pathlib import Path
import argparse, hashlib, json, urllib.request, zipfile
import pandas as pd
from app.pipeline import BASE, build

URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", type=Path)
    args = parser.parse_args()
    raw = BASE / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    xlsx = args.xlsx or raw / "Online Retail.xlsx"
    if not xlsx.exists():
        archive = raw / "online-retail.zip"
        if not archive.exists():
            print("Downloading UCI Online Retail...")
            urllib.request.urlretrieve(URL, archive)
        with zipfile.ZipFile(archive) as z:
            member = next(n for n in z.namelist() if n.endswith(".xlsx"))
            xlsx.write_bytes(z.read(member))
    if (
        not args.xlsx
        and hashlib.sha256(xlsx.read_bytes()).hexdigest()
        != "43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d"
    ):
        raise ValueError(
            "Dataset checksum changed. Inspect the upstream file before rebuilding."
        )
    print("Loading workbook and validating warehouse...")
    report = build(pd.read_excel(xlsx, engine="openpyxl"))
    report["source_sha256"] = hashlib.sha256(xlsx.read_bytes()).hexdigest()
    (BASE / "artifacts/quality.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
