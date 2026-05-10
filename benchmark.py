"""Run each of 12 query types N=10 times and report mean / p95 / min QTime.

Two configurations measured:
  distributed: query the books collection normally (Solr fan-outs to both shards)
  single_shard: same queries with distrib=false&shards=shard1 (one shard only,
                ~half the corpus, no shard merge)

Methodology:
  * Each query is run once cold (caches cleared between configurations) then
    9 more times warm. Reported numbers are over the 9 warm runs.
  * QTime as reported by Solr in responseHeader.QTime — measures Solr-side
    work only, excludes network round-trip.
  * Cache-clear: hit /admin/cores?action=RELOAD on each replica.
"""
import json
import statistics
import time
import urllib.parse
import urllib.request

BASE = "http://localhost:8983/solr/products/select"

QUERIES = [
    ("Q1 match-all", {"q": "*:*", "rows": 0}),
    ("Q2 edismax FT", {"q": "running", "defType": "edismax", "qf": "title^3 brand_text^2 description", "rows": 5}),
    ("Q3 fq+range", {"q": "*:*", "fq": ['category:"Electronics"', "price:[10 TO 50]"], "rows": 5}),
    ("Q4 facets", {"q": "*:*", "facet": "true", "facet.field": ["category", "brand"], "facet.mincount": 1, "rows": 0}),
    ("Q5 sort", {"q": "*:*", "sort": "rating desc, num_reviews desc", "rows": 5}),
    ("Q6 highlight", {"q": "description:wireless", "hl": "true", "hl.fl": "description", "rows": 5}),
    ("Q7 range facet", {"q": "*:*", "facet": "true", "facet.range": "price",
                         "facet.range.start": 0, "facet.range.end": 500,
                         "facet.range.gap": 50, "rows": 0}),
    ("Q8 phrase+bool", {"q": 'title:"running shoes" AND in_stock:true'}),
    ("Q9 fuzzy", {"q": "brand_text:Adidaz~2", "rows": 5}),
    ("Q10 boost", {"q": "{!boost b=rating}category:Electronics", "defType": "lucene", "rows": 5}),
    ("Q11 paging", {"q": "*:*", "start": 100, "rows": 10}),
    ("Q12 group", {"q": "*:*", "group": "true", "group.field": "category", "group.limit": 2, "rows": 0}),
]


def call(params):
    qs = urllib.parse.urlencode(params, doseq=True)
    url = f"{BASE}?{qs}&wt=json"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read())
    return data["responseHeader"]["QTime"]


def clear_cache():
    """Reload each replica core, which discards all caches."""
    # Best-effort: list cores from each node and reload them all
    import re as _re
    for port in (8983, 7574):
        try:
            data = urllib.request.urlopen(
                f"http://localhost:{port}/solr/admin/cores?action=STATUS&wt=json",
                timeout=5,
            ).read().decode()
            for core in _re.findall(r'"name":"(products[^"]*)"', data):
                try:
                    urllib.request.urlopen(
                        f"http://localhost:{port}/solr/admin/cores?action=RELOAD&core={core}",
                        timeout=10,
                    ).read()
                except Exception:
                    pass
        except Exception:
            pass
    # Pin loop variable to avoid shadowing the kept-out 'core' var
    for core in []:
        try:
            urllib.request.urlopen(
                f"http://localhost:8983/solr/admin/cores?action=RELOAD&core={core}",
                timeout=10,
            ).read()
        except Exception:
            pass
        try:
            urllib.request.urlopen(
                f"http://localhost:7574/solr/admin/cores?action=RELOAD&core={core}",
                timeout=10,
            ).read()
        except Exception:
            pass
    time.sleep(2)


def run_config(name, extra_params):
    print(f"\n=== {name} ===")
    print(f"  {'Query':<18} {'cold':>6} {'mean':>6} {'p95':>6} {'min':>6}  (ms)")
    print("  " + "-" * 60)
    rows = []
    clear_cache()
    for label, params in QUERIES:
        full = dict(params)
        full.update(extra_params)
        try:
            cold = call(full)
        except Exception as e:
            print(f"  {label:<18} ERR {e}")
            continue
        warm = []
        for _ in range(9):
            try:
                warm.append(call(full))
            except Exception:
                pass
        if warm:
            mean = statistics.mean(warm)
            p95 = sorted(warm)[int(len(warm) * 0.95) - 1] if len(warm) >= 2 else warm[0]
            mn = min(warm)
            rows.append((label, cold, mean, p95, mn))
            print(f"  {label:<18} {cold:>6} {mean:>6.1f} {p95:>6} {mn:>6}")
    return rows


def main():
    distributed = run_config("DISTRIBUTED (full books collection, 2 shards)", {})
    single = run_config("SINGLE-SHARD (distrib=false, shard1 only)",
                        {"distrib": "false", "shards": "shard1"})

    print("\n=== Comparison: mean QTime, distributed vs single-shard ===")
    print(f"  {'Query':<18} {'distrib':>10} {'single':>10}  speedup/overhead")
    print("  " + "-" * 60)
    s_map = {r[0]: r[2] for r in single}
    for label, _, mean_d, _, _ in distributed:
        mean_s = s_map.get(label)
        if mean_s is None:
            continue
        ratio = (mean_d / mean_s) if mean_s else 0
        tag = "OK" if ratio >= 0.9 else "single faster"
        print(f"  {label:<18} {mean_d:>10.1f} {mean_s:>10.1f}  ({ratio:.2f}x  {tag})")


if __name__ == "__main__":
    main()
