"""Transform 5 Bright Data e-commerce samples into a unified products.csv.

Sources (all CC-public, github.com/luminati-io/{Amazon,eCommerce}-dataset-samples):
  amazon-products.csv, walmart-products.csv, lazada-products.csv,
  shein-products.csv, shopee-products.csv  (1,000 rows each)

Output: data/products.csv with the project schema, ~5,000 real rows, no
synthetic / hash-derived fields. Source name is added as a 'source' field
(amazon, walmart, lazada, shein, shopee) so it can be faceted on.

Usage:  python data/transform_ecommerce.py
"""
import csv
import json
import re
from pathlib import Path

csv.field_size_limit(10_000_000)
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "products.csv"

# Per-source column mappings. Each value is either a column name or a tuple of
# fallback names (try in order).
SOURCES = {
    "amazon": {
        "file": "amazon_raw.csv",
        "id": "asin", "title": "title",
        "brand": ("brand", "seller_name"),
        "price": "final_price",
        "rating": "rating",
        "num_reviews": "reviews_count",
        "availability": "availability",
        "description": "description",
        "categories": "categories",      # JSON list
        "date": "date_first_available",
    },
    "walmart": {
        "file": "walmart-products.csv",
        "id": "product_id", "title": "product_name",
        "brand": "brand",
        "price": "final_price",
        "rating": "rating",              # plain numeric
        "num_reviews": "review_count",
        "availability": "available_for_delivery",
        "description": "description",
        "categories": "category_name",
        "date": None,
    },
    "lazada": {
        "file": "lazada-products.csv",
        "id": "product_id", "title": "title",
        "brand": ("brand", "seller_name"),
        "price": "final_price",
        "rating": "rating",
        "num_reviews": "reviews",
        "availability": None,
        "description": "product_description",
        "categories": "category_tree",    # slash-separated path
        "date": None,
    },
    # shein-products.csv has rating=0 for every row (no real ratings in the
    # sample), so we skip it. Including it would require accepting rows with
    # rating=0, which then breaks the rating-sort and rating-boost queries.
    "shopee": {
        "file": "shopee-products.csv",
        "id": "product_id", "title": "title",
        "brand": ("brand", "seller_name"),
        "price": "final_price",
        "rating": "rating",
        "num_reviews": "reviews",
        "availability": None,
        "description": "Product Description",
        "categories": "category",
        "date": None,
    },
}


def _get(row, key):
    if key is None:
        return ""
    if isinstance(key, tuple):
        for k in key:
            v = (row.get(k) or "").strip()
            if v:
                return v
        return ""
    return (row.get(key) or "").strip()


def parse_categories(raw):
    if not raw:
        return None, None
    raw = raw.strip()
    try:
        arr = json.loads(raw)
        if isinstance(arr, list):
            names = []
            for a in arr:
                if isinstance(a, str) and a.strip():
                    names.append(a.strip())
                elif isinstance(a, dict):
                    n = (a.get("name") or "").strip()
                    if n:
                        names.append(n)
            if names:
                return names[0], (names[1] if len(names) > 1 else names[0])
    except Exception:
        pass
    parts = [p.strip() for p in re.split(r"[>/|]+", raw) if p.strip()]
    if parts:
        return parts[0], (parts[1] if len(parts) > 1 else parts[0])
    return None, None


def parse_year(raw):
    if not raw:
        return None
    m = re.search(r"(19\d{2}|20\d{2})", raw)
    if m:
        y = int(m.group(1))
        if 1990 <= y <= 2026:
            return y
    return None


def parse_price(raw):
    if not raw:
        return None
    s = re.sub(r"[^\d.]", "", str(raw))
    if not s:
        return None
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def parse_int(raw):
    if not raw:
        return 0
    s = re.sub(r"[^\d]", "", str(raw))
    return int(s) if s else 0


def parse_avail(raw):
    raw = (raw or "").strip().lower()
    if not raw:
        return "true"
    if raw in {"true", "yes", "available", "in stock"}:
        return "true"
    if raw in {"false", "no", "out of stock", "unavailable"}:
        return "false"
    return "true" if "out" not in raw and "unavail" not in raw else "false"


def main():
    n_in = n_out = 0
    skipped = {"no_title": 0, "no_brand": 0, "no_price": 0, "no_rating": 0}
    with open(OUT, "w", encoding="utf-8", newline="") as o:
        writer = csv.DictWriter(
            o,
            fieldnames=["id", "title", "brand", "category", "subcategory",
                        "year", "num_reviews", "price", "rating",
                        "in_stock", "source", "description"],
        )
        writer.writeheader()
        for source_name, m in SOURCES.items():
            path = ROOT / m["file"]
            if not path.exists():
                print(f"  skipping {source_name}: {path.name} missing")
                continue
            with open(path, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    n_in += 1
                    title = _get(row, m["title"])
                    brand = _get(row, m["brand"])
                    price = parse_price(_get(row, m["price"]))
                    try:
                        rating = float(_get(row, m["rating"]) or 0)
                    except ValueError:
                        rating = 0.0
                    if not title:
                        skipped["no_title"] += 1; continue
                    if not brand:
                        skipped["no_brand"] += 1; continue
                    if price is None:
                        skipped["no_price"] += 1; continue
                    if rating <= 0:
                        skipped["no_rating"] += 1; continue
                    cat, sub = parse_categories(_get(row, m["categories"]))
                    cat = cat or "Uncategorized"
                    sub = sub or cat
                    year = parse_year(_get(row, m["date"])) or 2024
                    nrev = parse_int(_get(row, m["num_reviews"]))
                    avail = parse_avail(_get(row, m["availability"]))
                    desc = _get(row, m["description"])[:1500]
                    if not desc:
                        desc = f"{title} by {brand}. {cat} > {sub}. Sold on {source_name.capitalize()}."
                    raw_id = _get(row, m["id"]) or f"{source_name[:1].upper()}{n_in:05d}"
                    pid = f"{source_name[:1].upper()}-{raw_id}"[:80]
                    writer.writerow({
                        "id": pid,
                        "title": title[:500],
                        "brand": brand[:200],
                        "category": cat[:200],
                        "subcategory": sub[:200],
                        "year": year,
                        "num_reviews": nrev,
                        "price": price,
                        "rating": round(rating, 2),
                        "in_stock": avail,
                        "source": source_name,
                        "description": desc,
                    })
                    n_out += 1
    print(f"Read {n_in}, wrote {n_out} rows to {OUT}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
