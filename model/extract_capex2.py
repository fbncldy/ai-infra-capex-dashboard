import pdfplumber, os, re, glob

folder = "data/raw/alphabet"
# capex line with numbers, e.g. "Purchases of property and equipment (22,281) (31,485)"
num_re = re.compile(r"purchases of property and equipment.*?\(?\d[\d,]{3,}", re.I)

for path in sorted(glob.glob(os.path.join(folder, "*.pdf"))):
    name = os.path.basename(path)
    print(f"\n=== {name} ===")
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text() or ""
            low = txt.lower()
            if "consolidated statements of cash flows" in low or ("statements of cash flows" in low and "investing" in low):
                lines = txt.splitlines()
                # capture year header + capex line
                hdr = ""
                for ln in lines:
                    if re.search(r"20\d\d\s+20\d\d", ln):
                        hdr = ln.strip(); break
                for ln in lines:
                    if num_re.search(ln):
                        print(f"  p{i+1} hdr[{hdr[-40:]}]")
                        print(f"       {ln.strip()}")
