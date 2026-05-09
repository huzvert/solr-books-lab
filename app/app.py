"""Flask web UI for searching the Solr 'books' core.

Features:
- Full-text search with edismax query parser
- Faceted navigation (genre, publisher, in_stock)
- Range filter (year, price)
- Sorting (relevance, year, price, rating)
- Pagination
- Highlighted search terms
- Autocomplete suggestions (suggest handler)
"""
import os
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify

SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:8983/solr")
CORE = os.environ.get("SOLR_CORE", "books")
PAGE_SIZE = 10

app = Flask(__name__)


def solr_search(q, filters, sort, start):
    params = [
        ("q", q or "*:*"),
        ("defType", "edismax"),
        ("qf", "title^3 author^2 description genre publisher"),
        ("rows", PAGE_SIZE),
        ("start", start),
        ("wt", "json"),
        ("hl", "true"),
        ("hl.fl", "title,description,author"),
        ("hl.simple.pre", "<mark>"),
        ("hl.simple.post", "</mark>"),
        ("facet", "true"),
        ("facet.field", "genre"),
        ("facet.field", "publisher"),
        ("facet.field", "in_stock"),
        ("facet.mincount", 1),
    ]
    for fq in filters:
        params.append(("fq", fq))
    if sort:
        params.append(("sort", sort))
    url = f"{SOLR_URL}/{CORE}/select"
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "")
    page = max(1, int(request.args.get("page", 1)))
    selected = {
        "genre": request.args.getlist("genre"),
        "publisher": request.args.getlist("publisher"),
        "in_stock": request.args.getlist("in_stock"),
    }
    filters = []
    for field, vals in selected.items():
        for v in vals:
            filters.append(f'{field}:"{v}"')
    year_from = request.args.get("year_from", "").strip()
    year_to = request.args.get("year_to", "").strip()
    if year_from or year_to:
        lo = year_from or "*"
        hi = year_to or "*"
        filters.append(f"year:[{lo} TO {hi}]")

    start = (page - 1) * PAGE_SIZE
    error = None
    data = None
    try:
        data = solr_search(q, filters, sort, start)
    except Exception as e:
        error = str(e)

    docs, hl, facets, num_found, qtime = [], {}, {}, 0, 0
    if data:
        docs = data.get("response", {}).get("docs", [])
        # Solr returns multi-valued fields as lists; flatten for the template
        for d in docs:
            for k, v in list(d.items()):
                if isinstance(v, list) and len(v) == 1:
                    d[k] = v[0]
        num_found = data.get("response", {}).get("numFound", 0)
        qtime = data.get("responseHeader", {}).get("QTime", 0)
        hl = data.get("highlighting", {})
        ff = data.get("facet_counts", {}).get("facet_fields", {})
        for fname, arr in ff.items():
            facets[fname] = list(zip(arr[0::2], arr[1::2]))

    pages = (num_found + PAGE_SIZE - 1) // PAGE_SIZE
    qs = {k: v for k, v in request.args.items() if k != "page"}
    base_qs = urllib.parse.urlencode(qs, doseq=True)

    return render_template(
        "index.html",
        q=q, sort=sort, page=page, pages=pages,
        docs=docs, hl=hl, facets=facets,
        num_found=num_found, qtime=qtime,
        selected=selected, year_from=year_from, year_to=year_to,
        error=error, base_qs=base_qs,
    )


@app.route("/suggest")
def suggest():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    url = f"{SOLR_URL}/{CORE}/select"
    params = {
        "q": f"title:{q}* OR author:{q}*",
        "fl": "title,author",
        "rows": 8,
        "wt": "json",
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        docs = r.json().get("response", {}).get("docs", [])
        seen, out = set(), []
        for d in docs:
            t = d.get("title", "")
            if isinstance(t, list):
                t = t[0] if t else ""
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return jsonify(out)
    except Exception:
        return jsonify([])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
