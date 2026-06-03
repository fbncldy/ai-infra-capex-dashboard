import pdfplumber, os, re, glob

folder = "data/raw/alphabet"
patterns = [
    re.compile(r"purchases of property and equipment", re.I),
    re.compile(r"year ended december 31", re.I),
]

for path in sorted(glob.glob(os.path.join(folder, "*.pdf"))):
    name = os.path.basename(path)
    print(f"\n{'='*70}\n{name}\n{'='*70}")
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text() or ""
            if "purchases of property and equipment" in txt.lower() and "cash flow" in txt.lower():
                # print the page header years + the capex line
                lines = txt.splitlines()
                for ln in lines:
                    low = ln.lower()
                    if "year ended" in low or "purchases of property and equipment" in low:
                        print(f"  p{i+1}: {ln.strip()}")
                break
