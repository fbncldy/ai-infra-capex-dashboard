import pdfplumber, os, re, glob

folder = "data/raw/alphabet"
for path in sorted(glob.glob(os.path.join(folder, "*.pdf"))):
    name = os.path.basename(path)
    with pdfplumber.open(path) as pdf:
        npages = len(pdf.pages)
        first = pdf.pages[0].extract_text() or ""
        # try to find fiscal year on cover
        years = re.findall(r"(20\d\d)", first)
        # find period line
        period = ""
        for ln in first.splitlines():
            if "fiscal year ended" in ln.lower() or "year ended" in ln.lower() or "annual report" in ln.lower():
                period = ln.strip()
                break
        print(f"{name}: {npages} pages | coverhint='{period[:80]}' | years_on_cover={years[:6]}")
