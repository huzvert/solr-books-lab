"""Transform the Bright Data Amazon-products sample into the project schema.

Source: github.com/luminati-io/Amazon-dataset-samples (public e-commerce sample)
Output schema (all fields are real columns from the source):
    id, title, brand, category, subcategory, year, num_reviews,
    price, rating, in_stock, description

No synthetic / hash-derived fields — every value is read from the source row.
Rows missing any of {title, brand, final_price, rating} are dropped.

Usage:  python data/transform_amazon.py
"""
import csv
import json
import re
from pathlib import Path

csv.field_size_limit(10_000_000)

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "amazon_raw.csv"
OUT = ROOT / "products.csv"


def parse_categories(raw: str):
    """categories cell is a JSON array of strings (the breadcrumb path)."""
    if not raw:
        return None, None
    try:
        arr = json.loads(raw)
    except Exception:
        arr = None
    names = []
    if isinstance(arr, list):
        for a in arr:
            if isinstance(a, str) and a.strip():
                names.append(a.strip())
            elif isinstance(a, dict):
                n = (a.get("name") or "").strip()
                if n:
                    names.append(n)
    if names:
        return names[0], (names[1] if len(names) > 1 else names[0])
    parts = [p.strip() for p in re.split(r"[>/|]+", raw) if p.strip()]
    if parts:
        return parts[0], (parts[1] if len(parts) > 1 else parts[0])
    return None, None


def parse_year(raw: str):
    if not raw:
        return None
    m = re.search(r"(\d{4})", raw)
    if m:
        y = int(m.group(1))
        if 1990 <= y <= 2026:
            return y
    return None


def parse_price(raw: str):
    if not raw:
        return None
    s = re.sub(r"[^\d.]", "", str(raw))
    if not s:
        return None
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def main():
    n_in = n_out = 0
    skipped = {"no_title": 0, "no_brand": 0, "no_price": 0, "no_rating": 0}
    with open(RAW, "r", encoding="utf-8", newline="") as f, \
         open(OUT, "w", encoding="utf-8", newline="") as o:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(
            o,
            fieldnames=["id", "title", "brand", "category", "subcategory",
                        "year", "num_reviews", "price", "rating",
                        "in_stock", "description"],
        )
        writer.writeheader()
        for row in reader:
            n_in += 1
            title = (row.get("title") or "").strip()
            brand = (row.get("brand") or row.get("seller_name") or "").strip()
            price = parse_price(row.get("final_price"))
            try:
                rating = float(row.get("rating") or 0)
            except ValueError:
                rating = 0.0
            if not title:
                skipped["no_title"] += 1
                continue
            if not brand:
                skipped["no_brand"] += 1
                continue
            if price is None:
                skipped["no_price"] += 1
                continue
            if rating <= 0:
                skipped["no_rating"] += 1
                continue
            cat, subcat = parse_categories(row.get("categories", ""))
            cat = cat or "Uncategorized"
            subcat = subcat or cat
            year = parse_year(row.get("date_first_available", "")) or 2024
            try:
                num_reviews = int(re.sub(r"[^\d]", "", row.get("reviews_count") or "") or 0)
            except ValueError:
                num_reviews = 0
            avail = (row.get("availability") or "").lower()
            in_stock = "true" if (avail and "out" not in avail and "unavailable" not in avail) else "false"
            desc = (row.get("description") or "").strip()
            desc = desc[:1500] if len(desc) > 1500 else desc
            if not desc:
                desc = f"{title} by {brand}. {cat} > {subcat}. Sold on Amazon."
            asin = (row.get("asin") or "").strip() or f"P{n_in:05d}"
            writer.writerow({
                "id": asin,
                "title": title,
                "brand": brand,
                "category": cat,
                "subcategory": subcat,
                "year": year,
                "num_reviews": num_reviews,
                "price": price,
                "rating": round(rating, 2),
                "in_stock": in_stock,
                "description": desc,
            })
            n_out += 1
    print(f"Read {n_in}, wrote {n_out} rows to {OUT}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
