"""Demonstrate the second Solr ingestion path: XML over HTTP.

The lab manual lists three loading methods (Solr Cell/Tika, XML HTTP, Java
client API). The main pipeline uses CSV. This script shows the XML path on a
small auxiliary collection so the lab covers more than one ingest mode.

Usage:  python xml_ingest_demo.py
"""
import requests

SOLR = "http://localhost:8983/solr"
COL = "products_xml_demo"


def admin(action, **params):
    p = {"action": action, **params}
    r = requests.get(f"{SOLR}/admin/collections", params=p, timeout=30)
    return r.status_code, r.text


def main():
    # 1. Fresh collection
    print("[1/4] Creating collection ...")
    requests.get(f"{SOLR}/admin/collections",
                 params={"action": "DELETE", "name": COL}, timeout=30)
    requests.get(f"{SOLR}/admin/collections",
                 params={"action": "CREATE", "name": COL,
                         "numShards": 1, "replicationFactor": 1,
                         "collection.configName": "_default"}, timeout=30)

    # 2. Define the same minimal schema
    print("[2/4] Defining schema ...")
    fields = [
        {"name": "title", "type": "text_general", "stored": True, "indexed": True},
        {"name": "brand", "type": "string", "stored": True, "indexed": True},
        {"name": "price", "type": "pfloat", "stored": True, "indexed": True},
    ]
    for f in fields:
        try:
            requests.post(f"{SOLR}/{COL}/schema",
                          json={"add-field": f}, timeout=10)
        except Exception:
            pass

    # 3. Send three docs as XML, the Solr update XML format
    print("[3/4] Posting XML to /update ...")
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<add>
  <doc>
    <field name="id">XML001</field>
    <field name="title">Wireless Bluetooth Headphones</field>
    <field name="brand">Sony</field>
    <field name="price">79.99</field>
  </doc>
  <doc>
    <field name="id">XML002</field>
    <field name="title">Mechanical Keyboard RGB</field>
    <field name="brand">Logitech</field>
    <field name="price">129.50</field>
  </doc>
  <doc>
    <field name="id">XML003</field>
    <field name="title">USB-C Power Bank 20000mAh</field>
    <field name="brand">Anker</field>
    <field name="price">45.00</field>
  </doc>
</add>"""
    r = requests.post(
        f"{SOLR}/{COL}/update?commit=true",
        data=xml.encode("utf-8"),
        headers={"Content-Type": "application/xml"},
        timeout=15,
    )
    r.raise_for_status()

    # 4. Read back
    print("[4/4] Verifying ...")
    res = requests.get(f"{SOLR}/{COL}/select",
                       params={"q": "*:*", "rows": 5, "wt": "json"},
                       timeout=10).json()
    print(f"  numFound = {res['response']['numFound']}")
    for d in res["response"]["docs"]:
        t = d["title"][0] if isinstance(d.get("title"), list) else d.get("title")
        b = d["brand"][0] if isinstance(d.get("brand"), list) else d.get("brand")
        print(f"   * {d['id']}  [{b}]  {t}  ${d.get('price')}")

    print("\nDone. The XML ingestion path is identical to CSV at the request "
          "level — the Content-Type tells the update handler how to parse the "
          "body. The same /update endpoint accepts JSON too "
          "(Content-Type: application/json).")


if __name__ == "__main__":
    main()
