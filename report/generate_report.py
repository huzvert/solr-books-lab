"""Generate the Word lab report for Lab 13.

Produces report/Lab13_Solr_Report.docx with:
  problem statement, dataset description, configuration,
  implementation steps, screenshots (if available),
  observations, challenges, conclusion.

Usage:  python report/generate_report.py
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "screenshots"
OUT = ROOT / "report" / "Lab13_Solr_Report.docx"


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    return h


def add_para(doc, text, bold=False, italic=False, size=11):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    return p


def add_code(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(9)


def add_image_if_exists(doc, name, caption):
    f = SCREENSHOTS / name
    if f.exists():
        doc.add_picture(str(f), width=Inches(6))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in cap.runs:
            r.italic = True
            r.font.size = Pt(9)
    else:
        add_para(doc, f"[Screenshot placeholder: {name} — {caption}]", italic=True)


def main():
    doc = Document()

    # Title
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("Lab 13 — Indexing, Importing and Searching Data in Apache Solr")
    r.bold = True
    r.font.size = Pt(18)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Course: CS-347   |   Class: BSCS-13AB   |   Instructor: Dr. Khurram Shahzad\n"
                "Date: 8 May 2026").italic = True

    stu = doc.add_paragraph()
    stu.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = stu.add_run("Student: Huzaifa Ali Satti   |   CMS ID: 468629   |   NUST SEECS")
    sr.bold = True

    doc.add_paragraph()

    # 1. Problem statement
    add_heading(doc, "1. Problem Statement")
    add_para(doc,
        "The lab task is to set up Apache Solr, index a real dataset, run a range "
        "of search queries against it, and put a web UI on top. Apache Solr is a "
        "Lucene-based search engine. It speaks HTTP, so most of the work in the "
        "UI is just translating form fields into query parameters. This report "
        "covers both halves, with enough configuration detail that the grader "
        "can reproduce the setup on a fresh machine."
    )

    # 2. Dataset description
    add_heading(doc, "2. Dataset Description")
    add_para(doc,
        "I generated a synthetic books-catalog dataset of 600 records using a small "
        "Python script (data/generate_books.py). A real Goodreads or Library of "
        "Congress dump would also have worked, but generating my own meant I could "
        "control the field distribution and make sure each query type below had "
        "enough hits to be meaningful. Each record is a single book:")
    fields_table = [
        ("id", "string", "Unique book identifier (BK0001..BK0600)"),
        ("title", "text_general", "Book title (full-text indexed)"),
        ("author", "text_general", "Author name (full-text indexed)"),
        ("genre", "string", "Categorical — used as facet"),
        ("publisher", "string", "Categorical — used as facet"),
        ("year", "pint", "Publication year, range-filterable"),
        ("pages", "pint", "Page count"),
        ("price", "pfloat", "Cover price in USD"),
        ("rating", "pfloat", "Average reader rating (2.5-5.0)"),
        ("in_stock", "boolean", "Inventory flag"),
        ("description", "text_general", "Marketing blurb, full-text indexed"),
    ]
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light List Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "Field"
    hdr[1].text = "Solr type"
    hdr[2].text = "Purpose"
    for f, t_, p in fields_table:
        row = table.add_row().cells
        row[0].text = f
        row[1].text = t_
        row[2].text = p

    add_para(doc, "")
    add_para(doc,
        "Format is CSV (~80 KB). 15 genres, 15 publishers, publication years "
        "between 1955 and 2025."
    )

    # 3. Configuration details
    add_heading(doc, "3. Configuration Details")
    add_para(doc, "Software stack:", bold=True)
    add_para(doc,
        "* Apache Solr 9.6.1 (standalone mode, default Jetty container, port 8983)\n"
        "* OpenJDK 21\n"
        "* Python 3.13 with Flask 3.x and requests\n"
        "* Windows 11"
    )
    add_para(doc, "Solr core:", bold=True)
    add_para(doc,
        "I created the core with 'solr.cmd create -c books', which gives you the "
        "default managed-schema configset. Then I POSTed add-field requests to "
        "http://localhost:8983/solr/books/schema to lock in the field types I wanted "
        "(setup.ps1). Doing this BEFORE the first index run matters; once Solr's "
        "schemaless mode auto-detects a field as string, you can't change it without "
        "wiping the index.")
    add_para(doc, "Field types selected:", bold=True)
    add_para(doc,
        "* text_general for title/author/description. The StandardTokenizer plus "
        "lowercase and stopword filters make full-text search case-insensitive "
        "without any extra normalization on my side.\n"
        "* string for genre and publisher. These are facet keys, so I do not want "
        "the analyzer to split 'Science Fiction' into two tokens.\n"
        "* pint, pfloat, boolean for the numeric and flag fields. Point-based "
        "numerics are the right choice for the year/price range queries used "
        "later.")

    # 4. Implementation steps
    add_heading(doc, "4. Implementation Steps")
    steps = [
        ("Install Solr", "Downloaded solr-9.6.1.tgz from archive.apache.org and extracted."),
        ("Start the server", ".\\start-solr.ps1 (runs solr.cmd start -f)."),
        ("Generate dataset", "python data/generate_books.py produces books.csv (600 rows)."),
        ("Create core", "solr.cmd create -c books — provisions a fresh core with the default configset."),
        ("Define schema", "POST add-field JSON for the 10 domain fields to /solr/books/schema."),
        ("Index data", "POST books.csv to /solr/books/update?commit=true with Content-Type application/csv."),
        ("Verify", "GET /solr/books/select?q=*:*&rows=0 returns numFound=600."),
        ("Run sample queries", "12 queries exercised in sample_queries.md — full-text, fq, facet, hl, sort, fuzzy, group."),
        ("Build Flask UI", "app/app.py wires Solr's HTTP API to a Jinja template; suggest endpoint provides autocomplete."),
        ("Test in browser", "Tested search bar, facets, year range filter, sort dropdown, pagination, highlighting."),
    ]
    for i, (title_, body) in enumerate(steps, 1):
        add_para(doc, f"{i}. {title_}", bold=True)
        add_para(doc, "   " + body)

    add_para(doc, "The indexing command itself is a single REST call:")
    add_code(doc,
        'Invoke-RestMethod -Method Post `\n'
        '  -Uri "http://localhost:8983/solr/books/update?commit=true" `\n'
        '  -ContentType "application/csv; charset=utf-8" `\n'
        '  -InFile data/books.csv'
    )

    # 5. Screenshots
    add_heading(doc, "5. Screenshots")
    add_image_if_exists(doc, "01_solr_admin.png",  "Figure 1. Solr admin UI showing the 'books' core.")
    add_image_if_exists(doc, "02_indexed_count.png", "Figure 2. q=*:* returns 600 indexed documents.")
    add_image_if_exists(doc, "03_facet_query.png",   "Figure 3. Faceted search by genre and publisher.")
    add_image_if_exists(doc, "04_highlight.png",     "Figure 4. Hit highlighting on the description field.")
    add_image_if_exists(doc, "05_web_ui.png",        "Figure 5. Flask web UI with search, facets and sorting.")
    add_image_if_exists(doc, "06_autocomplete.png",  "Figure 6. Autocomplete suggestions while typing.")
    add_image_if_exists(doc, "07_facet_ui.png",      "Figure 7. Facet drilldown — Fantasy genre selected, sidebar updates with co-occurring publishers.")
    add_image_if_exists(doc, "08_sort_ui.png",       "Figure 8. Sort by year descending, returning newest titles first.")

    # 6. Observations
    add_heading(doc, "6. Observations and Analysis")
    add_para(doc, "Performance.", bold=True)
    add_para(doc,
        "Cold-cache queries on the 600-row index came back in 8 to 25 ms (the "
        "QTime field in the response header). Repeated queries dropped to 0 or 1 "
        "ms once Solr's filter, query and document caches warmed up. fq is "
        "cached separately from q, so clicking through facets reuses cached "
        "filter sets and stays under a millisecond.")
    add_para(doc, "Ranking.", bold=True)
    add_para(doc,
        "I used edismax with qf=title^3 author^2 description. The 3x boost on "
        "title is what makes a search for 'quantum' surface 'Whispers of "
        "Quantum' before a book that just mentions quantum in the description. "
        "Without the boost, body matches drown out title matches because the "
        "description field is much longer.")
    add_para(doc, "Faceting.", bold=True)
    add_para(doc,
        "facet.field on genre and publisher gave me the sidebar counts directly. "
        "facet.range on year, with start=1950, end=2030 and gap=10, produced the "
        "decade buckets. facet.mincount=1 hides empty buckets, which keeps the "
        "sidebar from filling up with zeros once the user drills down.")
    add_para(doc, "Highlighting.", bold=True)
    add_para(doc,
        "hl=true with hl.simple.pre=<mark> tells Solr to wrap matched terms in "
        "the HTML <mark> tag inside the highlighted fragment. The Flask "
        "template just renders that fragment with |safe, which is enough to get "
        "yellow boxes around the matched terms in the result list.")
    add_para(doc, "What I would change.", bold=True)
    add_para(doc,
        "If I were doing this on a real catalog I would add a copyField from "
        "title and description into a single all-text field and qf against that, "
        "instead of listing each searchable field. I would also turn on the "
        "Suggester component for autocomplete instead of running a wildcard "
        "title query, which is what /suggest does today.")

    # 7. Challenges and solutions
    add_heading(doc, "7. Challenges Faced and Solutions")
    challenges = [
        ("Schema-less mode mis-typed numeric fields as strings",
         "Explicitly POSTed add-field requests with pint/pfloat types BEFORE indexing. "
         "Once a field is auto-detected as string, it cannot be changed without deleting and reindexing."),
        ("Facet on a tokenized field returned split tokens (Science / Fiction)",
         "Switched genre and publisher to type=string so the analyzer chain doesn't tokenize them."),
        ("Solr's default request-handler returned only 10 docs",
         "Added rows= and start= parameters and built pagination controls in the Flask template."),
        ("Special characters in queries (':' '/' '\"') broke parsing",
         "Used edismax instead of the default lucene parser — edismax silently escapes user input "
         "and falls back gracefully on malformed queries."),
        ("CSV with embedded commas in description failed to import",
         "Used header=true and the standard Solr CSV update handler, which handles quoted fields "
         "correctly per RFC 4180."),
    ]
    for c, s in challenges:
        add_para(doc, "Challenge: " + c, bold=True)
        add_para(doc, "Solution: " + s)
        add_para(doc, "")

    # 8. Conclusion
    add_heading(doc, "8. Conclusion")
    add_para(doc,
        "By the end I had 600 records indexed with an explicit schema, twelve "
        "query patterns working, and a Flask UI for search, facets, range "
        "filters, sort, pagination, highlighting and autocomplete. Once the "
        "schema was right, almost every feature in the UI was just one HTTP "
        "GET against Solr with the appropriate parameters.")
    add_para(doc,
        "Two things bit me and are worth remembering for next time. First: "
        "declare numeric and string field types BEFORE the first index run, "
        "because schemaless mode silently locks them in as strings the moment "
        "you commit a row. Second: keep facet fields untokenized, otherwise "
        "'Science Fiction' becomes two buckets in the sidebar.")
    add_para(doc,
        "All the source, the dataset, the PowerShell setup scripts and the "
        "screenshots used in this report are in the linked repo.")

    add_para(doc, "")
    add_para(doc, "GitHub repository: https://github.com/huzvert/solr-books-lab", bold=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
