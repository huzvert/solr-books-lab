"""Run the 12 sample queries against Solr and print a summary.

Used during the lab to demonstrate each query type works and to capture
QTime numbers for the report. Run AFTER setup.ps1 has indexed the data.

    python verify_queries.py
"""
import requests
import json

BASE = "http://localhost:8983/solr/books/select"


def run(name, params, show_docs=False):
    r = requests.get(BASE, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    qt = data["responseHeader"]["QTime"]
    if "grouped" in data:
        g = data["grouped"]
        gname = next(iter(g))
        n = g[gname].get("matches", 0)
        print(f"\n--- {name} ---\n  matches={n}, QTime={qt}ms (grouped on {gname})")
        for grp in g[gname].get("groups", [])[:5]:
            print(f"   group {grp['groupValue']}: {grp['doclist']['numFound']} docs")
        return
    n = data["response"]["numFound"]
    print(f"\n--- {name} ---")
    print(f"  numFound={n}, QTime={qt}ms")
    if show_docs:
        for d in data["response"]["docs"][:3]:
            t = d.get("title")
            t = t[0] if isinstance(t, list) else t
            print(f"   * {d.get('id')}  {t}")
    if "facet_counts" in data:
        ff = data["facet_counts"]["facet_fields"]
        for fname, arr in ff.items():
            top = list(zip(arr[0::2], arr[1::2]))[:5]
            print(f"  facet {fname}: {top}")
    if "highlighting" in data:
        for k, v in list(data["highlighting"].items())[:1]:
            print(f"  hl {k}: {v}")


if __name__ == "__main__":
    run("Q1 match-all", {"q": "*:*", "rows": 0})
    run("Q2 edismax full-text", {
        "q": "quantum machine", "defType": "edismax",
        "qf": "title^3 author^2 description", "rows": 3,
    }, show_docs=True)
    run("Q3 fq genre + price range", {
        "q": "*:*", "fq": ['genre:"Science Fiction"', "price:[10 TO 30]"], "rows": 3,
    }, show_docs=True)
    run("Q4 facet by genre/publisher", {
        "q": "*:*", "facet": "true",
        "facet.field": ["genre", "publisher"],
        "facet.mincount": 1, "rows": 0,
    })
    run("Q5 sort by year desc", {
        "q": "*:*", "sort": "year desc, rating desc", "rows": 3,
    }, show_docs=True)
    run("Q6 highlighting", {
        "q": "description:freedom", "hl": "true", "hl.fl": "description",
        "hl.simple.pre": "<mark>", "hl.simple.post": "</mark>", "rows": 1,
    })
    run("Q7 range facet by decade", {
        "q": "*:*", "facet": "true", "facet.range": "year",
        "facet.range.start": 1950, "facet.range.end": 2030,
        "facet.range.gap": 10, "rows": 0,
    })
    run("Q8 phrase + boolean", {"q": 'title:"Lost Kingdom" AND in_stock:true'})
    run("Q9 fuzzy author", {"q": "author:Smyth~2", "rows": 3}, show_docs=True)
    run("Q10 boost by rating", {
        "q": "{!boost b=rating}genre:Fantasy", "defType": "lucene", "rows": 3,
    }, show_docs=True)
    run("Q11 pagination start=20", {"q": "*:*", "start": 20, "rows": 5})
    run("Q12 group by genre", {
        "q": "*:*", "group": "true", "group.field": "genre", "group.limit": 2,
    })
    print("\nAll 12 queries executed.")
