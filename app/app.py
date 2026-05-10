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
CORE = os.environ.get("SOLR_CORE", "products")
PAGE_SIZE = 10

app = Flask(__name__)


def solr_search(q, filters, sort, start):
    params = [
        ("q", q or "*:*"),
        ("defType", "edismax"),
        ("qf", "title^3 brand_text^2 description category subcategory"),
        ("rows", PAGE_SIZE),
        ("start", start),
        ("wt", "json"),
        ("hl", "true"),
        ("hl.fl", "title,description"),
        ("hl.simple.pre", "<mark>"),
        ("hl.simple.post", "</mark>"),
        ("facet", "true"),
        ("facet.field", "category"),
        ("facet.field", "brand"),
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
        "category": request.args.getlist("category"),
        "brand": request.args.getlist("brand"),
        "in_stock": request.args.getlist("in_stock"),
    }
    filters = []
    for field, vals in selected.items():
        for v in vals:
            filters.append(f'{field}:"{v}"')
    price_from = request.args.get("price_from", "").strip()
    price_to = request.args.get("price_to", "").strip()
    if price_from or price_to:
        lo = price_from or "*"
        hi = price_to or "*"
        filters.append(f"price:[{lo} TO {hi}]")

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
        selected=selected, price_from=price_from, price_to=price_to,
        error=error, base_qs=base_qs,
    )


@app.route("/api/search")
def api_search():
    """JSON search endpoint for live, fetch-on-keystroke result rendering."""
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "")
    page = max(1, int(request.args.get("page", 1)))
    selected = {
        "category": request.args.getlist("category"),
        "brand": request.args.getlist("brand"),
        "in_stock": request.args.getlist("in_stock"),
    }
    filters = []
    for field, vals in selected.items():
        for v in vals:
            filters.append(f'{field}:"{v}"')
    price_from = request.args.get("price_from", "").strip()
    price_to = request.args.get("price_to", "").strip()
    if price_from or price_to:
        filters.append(f"price:[{price_from or '*'} TO {price_to or '*'}]")
    start = (page - 1) * PAGE_SIZE
    try:
        data = solr_search(q, filters, sort, start)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    docs = data.get("response", {}).get("docs", [])
    for d in docs:
        for k, v in list(d.items()):
            if isinstance(v, list) and len(v) == 1:
                d[k] = v[0]
    hl = data.get("highlighting", {})
    ff = data.get("facet_counts", {}).get("facet_fields", {})
    facets = {fname: list(zip(arr[0::2], arr[1::2])) for fname, arr in ff.items()}
    return jsonify({
        "numFound": data.get("response", {}).get("numFound", 0),
        "qtime": data.get("responseHeader", {}).get("QTime", 0),
        "docs": docs,
        "highlighting": hl,
        "facets": facets,
        "page": page,
        "pageSize": PAGE_SIZE,
    })


@app.route("/suggest")
def suggest():
    """Autocomplete via Solr's SuggestComponent (AnalyzingInfixLookupFactory)
    over the title field. Falls back to a wildcard query if the suggester
    handler isn't configured (older deployments)."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    # Primary: SuggestComponent
    try:
        r = requests.get(
            f"{SOLR_URL}/{CORE}/suggest_handler",
            params={"suggest.q": q, "wt": "json", "suggest.count": 8},
            timeout=5,
        )
        r.raise_for_status()
        sug = r.json().get("suggest", {}).get("titleSuggester", {})
        bucket = next(iter(sug.values()), {})
        items = bucket.get("suggestions", [])
        # Strip the <b>...</b> wrapping the matched substring
        out, seen = [], set()
        for s in items:
            term = s.get("term", "").replace("<b>", "").replace("</b>", "")
            if term and term not in seen:
                seen.add(term)
                out.append(term)
        if out:
            return jsonify(out)
    except Exception:
        pass
    # Fallback: wildcard query
    try:
        r = requests.get(
            f"{SOLR_URL}/{CORE}/select",
            params={
                "q": f"title:{q}* OR author:{q}*",
                "fl": "title,author",
                "rows": 8,
                "wt": "json",
            },
            timeout=5,
        )
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
