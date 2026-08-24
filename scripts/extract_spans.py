"""Extract raw color-tagged text spans (with bounding boxes) from every page
of the source calendar PDF, and dump them to a JSON file for downstream
parsing. Kept as a separate step so the (slow, one-time) PDF read is cached.
"""
import fitz
import json
import sys

SRC = r"C:\Users\Owner\OneDrive\Desktop\calendar 2000-2100-010 2021.pdf"
OUT = r"C:\Dev\nasi-calendar\data\raw_spans.json"


def main():
    doc = fitz.open(SRC)
    pages_out = []
    for pno in range(doc.page_count):
        page = doc[pno]
        d = page.get_text("dict")
        spans = []
        for block in d["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    text = span["text"]
                    if not text.strip():
                        continue
                    x0, y0, x1, y1 = span["bbox"]
                    spans.append({
                        "t": text,
                        "c": span["color"],
                        "x0": round(x0, 2),
                        "x1": round(x1, 2),
                        "top": round(y0, 2),
                        "bottom": round(y1, 2),
                    })
        pages_out.append(spans)
        print(f"page {pno}: {len(spans)} spans", file=sys.stderr)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(pages_out, f, ensure_ascii=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
