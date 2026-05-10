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
        "The dataset is the open Goodbooks-10K corpus "
        "(github.com/zygmuntz/goodbooks-10k), a public-domain CSV of the 10,000 "
        "most-rated books on Goodreads. After dropping rows with a missing or "
        "out-of-range publication year I had 9,929 usable records. The script at "
        "data/transform_goodbooks.py reshapes the raw columns into the project's "
        "schema. The real fields (title, author, year, rating, language) are "
        "kept verbatim. Three fields the original dataset does not provide "
        "(publisher, page count, price, in_stock) are filled in deterministically "
        "from a hash of book_id so the price-range filter and stock facet in the "
        "UI still demonstrate something. This is documented honestly in the "
        "transform script and in the README.")
    add_para(doc, "Each record is a single book with these fields:")
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
        "Source: github.com/zygmuntz/goodbooks-10k (CC0). Format: CSV, 9,929 rows, "
        "~2 MB after transformation. Genre buckets correspond to the language_code "
        "of the original record (English dominates with 7,368 books, followed by "
        "English (US) with 2,061; smaller buckets cover Spanish, French, German, "
        "Arabic, Japanese and others). Publication years span 1500-2025."
    )

    # 3. Configuration details
    add_heading(doc, "3. Configuration Details")
    add_para(doc, "Software stack:", bold=True)
    add_para(doc,
        "* Apache Solr 9.6.1 (SolrCloud mode, 2 nodes, embedded ZooKeeper)\n"
        "* OpenJDK 21\n"
        "* Python 3.13 with Flask 3.x and requests\n"
        "* Windows 11"
    )
    add_para(doc, "Cluster topology:", bold=True)
    add_para(doc,
        "I started Solr with 'solr.cmd -e cloud -noprompt', which provisions a "
        "two-node cluster: node1 on port 8983 and node2 on port 7574, with an "
        "embedded ZooKeeper instance on port 9983 coordinating cluster state. "
        "The 'books' collection is created with numShards=2 and "
        "replicationFactor=2, giving 4 cores total: each shard has a leader on "
        "one node and a replica on the other. With ~9,929 documents this puts "
        "roughly 5,000 documents in each shard. The Flask UI continues to talk "
        "to a single endpoint (http://localhost:8983/solr/books/select); Solr "
        "transparently fan-outs the query to both shards and merges the results.")
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
        ("Start a SolrCloud cluster", ".\\solr-9.6.1\\bin\\solr.cmd -e cloud -noprompt brings up 2 nodes (8983, 7574) with embedded ZooKeeper on 9983."),
        ("Download dataset", "curl https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv into data/goodbooks_raw.csv (10,000 rows)."),
        ("Transform dataset", "python data/transform_goodbooks.py maps raw columns into the project schema and drops 71 rows with bad publication years (9,929 valid rows out)."),
        ("Create sharded collection", "POST /solr/admin/collections?action=CREATE&name=books&numShards=2&replicationFactor=2&collection.configName=_default — gives 4 cores spread across the two nodes."),
        ("Define schema", "POST add-field JSON for the 10 domain fields to /solr/books/schema."),
        ("Index data", "POST books.csv to /solr/books/update?commit=true&header=true with Content-Type application/csv. Indexed in 4.7 seconds."),
        ("Verify shard distribution", "Each shard ends up holding ~4,978 of the 9,929 docs. Hash-based routing on the id field gives a near-50/50 split."),
        ("Run sample queries", "12 query types exercised in sample_queries.md — full-text edismax, fq, facet, range facet, hl, fuzzy, function-query boost, grouping."),
        ("Field-types experiment", "Created a separate 'books_bad' collection with genre as text_general instead of string to demonstrate empirically why the choice matters (see Observations 6.5 below)."),
        ("Build Flask UI", "app/app.py wires Solr's HTTP API to a Jinja template; the /suggest endpoint provides autocomplete."),
        ("Test in browser", "Search, facets, year-range filter, sort dropdown, pagination, highlighting all verified manually with real queries (Harry Potter, quantum, etc.)."),
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
    add_image_if_exists(doc, "01_solr_admin.png",  "Figure 1. Solr Admin UI dashboard showing the running SolrCloud instance.")
    add_image_if_exists(doc, "09_solrcloud_topology.png", "Figure 2. SolrCloud Cloud > Nodes view: two nodes (ports 8983 and 7574), each hosting two replicas of the sharded 'books' collection.")
    add_image_if_exists(doc, "11_query_tab.png",   "Figure 3. Solr Admin > Query tab on the books collection — the in-browser query builder used for ad-hoc testing during development.")
    add_image_if_exists(doc, "10_schema_tab.png",  "Figure 4. Schema tab for the 'genre' field on the books (production) collection. Field-Type is StrField (string), Tokenized=NO. This is the production-correct setting.")
    add_image_if_exists(doc, "13_field_experiment_bad_schema.png", "Figure 5. Schema tab for the same field on the books_bad collection: Field-Type is text_general, Tokenized=YES. Used as the deliberate-misconfiguration baseline for the field-types experiment in Section 6.")
    add_image_if_exists(doc, "02_indexed_count.png", "Figure 6. q=*:* against the books collection returns numFound=9929 (across both shards).")
    add_image_if_exists(doc, "03_facet_query.png",   "Figure 7. Faceted search by genre and publisher — the distributed query merges counts from both shards.")
    add_image_if_exists(doc, "04_highlight.png",     "Figure 8. Hit highlighting wraps matched terms with <mark> tags in the description field.")
    add_image_if_exists(doc, "12_field_experiment.png", "Figure 9. Broken facet output from books_bad: the StandardTokenizer split 'Science Fiction' and 'Historical Fiction' into individual tokens, and the two 'fiction' tokens collapsed into a single bucket of 4. The genre information is destroyed.")
    add_image_if_exists(doc, "05_web_ui.png",        "Figure 10. Flask web UI: a search for 'potter' returns the Harry Potter series with highlighted hits, sidebar facets, and full metadata.")
    add_image_if_exists(doc, "06_autocomplete.png",  "Figure 11. Search results for the query 'harry'.")
    add_image_if_exists(doc, "07_facet_ui.png",      "Figure 12. Facet drilldown: filtering on genre = English (UK) updates the result list and the sidebar's co-occurring publishers.")
    add_image_if_exists(doc, "08_sort_ui.png",       "Figure 13. Sort by year descending returns the newest titles first.")
    add_image_if_exists(doc, "14_live_search.png",   "Figure 14. Live search-as-you-type. The result list re-renders on every keystroke via fetch to /api/search, and history.replaceState keeps the URL in sync so any state remains shareable.")
    add_image_if_exists(doc, "15_failover_before.png", "Figure 15. Cluster topology before the failover test: both nodes (8983 and 7574) live, books collection's four replicas (s1r4, s1r6, s2r1, s2r2) spread across them.")
    add_image_if_exists(doc, "16_failover_after.png", "Figure 16. Same view after running 'solr.cmd stop -p 7574'. Only one node is live; the books collection is still fully available because each shard has a replica on the surviving node.")
    add_image_if_exists(doc, "17_failover_query.png", "Figure 17. Flask web UI search for 'potter' returns all 29 results while node2 is down — confirming fault-tolerant distributed search.")
    add_image_if_exists(doc, "18_failover_json.png", "Figure 18. Raw Solr JSON response for the same query during the failover, captured directly from the surviving node1 endpoint.")
    add_image_if_exists(doc, "19_suggester.png",      "Figure 19. SuggestComponent response for suggest.q=harry — returns full title strings with the matched substring wrapped in <b>...</b> via AnalyzingInfixLookupFactory.")

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
    add_para(doc, "Field-types experiment.", bold=True)
    add_para(doc,
        "To convince myself the schema choices in section 3 actually mattered, I "
        "created a second collection 'books_bad' on a separate configset, "
        "declared its 'genre' field as text_general instead of string, and "
        "indexed six identical rows covering three multi-word genres (Science "
        "Fiction x2, Historical Fiction x2, Crime Thriller x2).")
    add_para(doc,
        "books_bad facet output (Figure 9): "
        "'fiction' -> 4, 'crime' -> 2, 'historical' -> 2, 'science' -> 2, "
        "'thriller' -> 2.")
    add_para(doc,
        "The StandardTokenizer chained into text_general split each multi-word "
        "value on whitespace and lowercased the tokens. 'Science Fiction' "
        "became {science, fiction}, 'Historical Fiction' became {historical, "
        "fiction}, and the two 'fiction' tokens collapsed into one bucket of 4 "
        "documents. The genre information needed for the sidebar is gone.")
    add_para(doc,
        "books (production) facet output for comparison: "
        "'English' -> 7368, 'English (US)' -> 2061, 'English (UK)' -> 256, ...")
    add_para(doc,
        "string fields skip the analyzer chain, so each value is stored "
        "byte-for-byte. The buckets stay intact and the UI sidebar gets the "
        "counts it needs.")
    add_para(doc,
        "Side-finding while running this experiment: replacing genre's type on "
        "an already-indexed collection produced this Lucene error on the next "
        "write — 'cannot change field genre from index options=DOCS to "
        "inconsistent index options=DOCS_AND_FREQS_AND_POSITIONS'. So the "
        "rule is firmer than I expected: declare the type before the first "
        "index run, or be prepared to delete the collection and start over.")

    add_para(doc, "Fault tolerance (failover demo).", bold=True)
    add_para(doc,
        "I tested the cluster's tolerance to a node failure. Starting from "
        "both nodes up and 9,929 documents indexed, I stopped node2 with "
        "'solr.cmd stop -p 7574' and re-ran the production queries against "
        "the surviving node1 endpoint. The cluster status reported live_nodes "
        "= ['localhost:8983_solr'] (only one node), but queries continued to "
        "return correct results: q=*:* still numFound=9929, edismax q=potter "
        "still numFound=29 with the Harry Potter series at the top. This works "
        "because each shard has replicationFactor=2, so the data is mirrored "
        "across both nodes; node1 already holds a full replica of every "
        "shard. After verification I restarted node2 and the cluster returned "
        "to its original 2-node state with no manual intervention. See "
        "Figures 15-18 in the screenshots section.")

    add_para(doc, "Performance methodology and shard-overhead measurement.", bold=True)
    add_para(doc,
        "I wrote benchmark.py (in the repo root) which runs each of the 12 "
        "query patterns 10 times: one cold call after a core RELOAD to clear "
        "all caches, then 9 warm runs. QTime is read from the response "
        "header (Solr-side cost only, excluding network round-trip). The "
        "same 12 queries were run in two configurations against the same "
        "9,929-document collection: distributed (Solr fan-outs to both "
        "shards and merges) and single-shard (distrib=false, hits one "
        "shard's ~5,000 docs). Mean and p95 QTime over the 9 warm runs are "
        "reported.")
    add_para(doc, "Selected results (mean QTime over 9 warm runs, in ms):")
    table = doc.add_table(rows=1, cols=4)
    table.style = "Light List Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "Query"
    hdr[1].text = "distributed (2 shards)"
    hdr[2].text = "single-shard"
    hdr[3].text = "ratio"
    rows = [
        ("Q1 match-all",       "11.1", "0.4",  "25x"),
        ("Q2 edismax full-text","24.9", "2.6",  "10x"),
        ("Q3 fq + price range","19.9", "0.7",  "30x"),
        ("Q4 multi-field facets","15.0","4.7",  "3x"),
        ("Q5 sort year+rating","37.0", "1.1",  "33x"),
        ("Q6 highlighting",    "29.6", "9.4",  "3x"),
        ("Q9 fuzzy",           "22.7", "1.6",  "15x"),
        ("Q11 paging start=100","28.4","0.8", "37x"),
    ]
    for q, d_, s_, r_ in rows:
        rc = table.add_row().cells
        rc[0].text = q
        rc[1].text = d_
        rc[2].text = s_
        rc[3].text = r_
    add_para(doc, "Interpretation.", bold=True)
    add_para(doc,
        "Distributed wins zero of the twelve queries. It's 3x to 37x slower "
        "than the single-shard equivalent across the board. The reason is "
        "boring once you look at the single-shard column: each shard's work "
        "is already sub-millisecond. There is nothing to parallelize. The "
        "coordinator still has to fan out, wait for the slowest replica, "
        "and merge the responses, and that overhead is what we are actually "
        "measuring.")
    add_para(doc,
        "Sharding starts to pay off when the per-shard work is expensive "
        "enough to make the coordinator cost look small. For Lucene that "
        "usually means millions of documents, not ten thousand. For this "
        "lab the cluster was worth setting up because the prerequisite "
        "asked for it and because it lets me demonstrate failover, but I "
        "would not run a 10K-record catalog this way in production. "
        "Per-query numbers including p95 are in report/benchmark_results.txt.")

    add_para(doc, "Suggester component (autocomplete).", bold=True)
    add_para(doc,
        "After the empirical benchmark I replaced the original wildcard-"
        "based autocomplete with Solr's proper SuggestComponent. I posted "
        "this configuration to /solr/books/config:")
    add_code(doc,
        '{"add-searchcomponent":{\n'
        '   "name":"suggest_component",\n'
        '   "class":"solr.SuggestComponent",\n'
        '   "suggester":{\n'
        '     "name":"titleSuggester",\n'
        '     "lookupImpl":"AnalyzingInfixLookupFactory",\n'
        '     "dictionaryImpl":"DocumentDictionaryFactory",\n'
        '     "field":"title",\n'
        '     "suggestAnalyzerFieldType":"text_general",\n'
        '     "buildOnCommit":"true"\n'
        '   }},\n'
        ' "add-requesthandler":{\n'
        '   "name":"/suggest_handler",\n'
        '   "class":"solr.SearchHandler",\n'
        '   "defaults":{"suggest":"true","suggest.count":"10",\n'
        '              "suggest.dictionary":"titleSuggester"},\n'
        '   "components":["suggest_component"]}\n'
        '}')
    add_para(doc,
        "AnalyzingInfixLookupFactory does prefix AND infix matching against "
        "the analyzed title field, so 'harry' matches 'The Lincoln Lawyer "
        "(Mickey Haller, #1; Harry Bosch Universe, #16)' as well as 'Harry "
        "Potter and the Sorcerer's Stone'. The Flask /suggest endpoint now "
        "calls the Suggester first and falls back to the wildcard query if "
        "the handler isn't configured (older deployments). See Figure 19.")
    add_para(doc, "Side-finding while configuring this:", bold=True)
    add_para(doc,
        "The first time I posted this config I sent buildOnCommit: true as a "
        "JSON boolean and got a 500 back. The Solr server log had the real "
        "story: 'class java.lang.Boolean cannot be cast to class "
        "java.lang.String' inside SuggestComponent.inform(). Quoting it as "
        "\"true\" worked immediately. The schema and config APIs accept JSON "
        "but pass several values through string parsers internally, so any "
        "unquoted boolean or number can hit this.")

    add_para(doc, "Live search-as-you-type.", bold=True)
    add_para(doc,
        "The Flask UI exposes a JSON endpoint at /api/search that returns the "
        "same result set as the rendered page. The frontend debounces input "
        "events on the search box (180 ms) and re-renders the result list on "
        "every keystroke, without reloading the page. history.replaceState "
        "keeps the URL in sync so any state (query, facets, sort) is still "
        "shareable. The traditional form submit also still works as a "
        "no-JavaScript fallback.")

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
        "By the end I had a 2-node SolrCloud cluster holding 9,929 real "
        "Goodreads books across two shards, with replicas mirrored so a "
        "node failure does not take queries down. Twelve query patterns "
        "work against the distributed collection. The Flask UI on top "
        "covers search, facets, range filters, sort, pagination, "
        "highlighting, real autocomplete (via SuggestComponent), and "
        "search-as-you-type.")
    add_para(doc,
        "Two findings I want to keep from the empirical work. First, "
        "schema choices are load-bearing in a way I did not appreciate "
        "before: declaring genre as text_general silently splits "
        "multi-word values across separate facet buckets. Second, "
        "sharding at this corpus size is a net loss. The distributed "
        "version of every query I ran was 3 to 37 times slower than the "
        "single-shard equivalent because the coordinator overhead is the "
        "dominant cost when the per-shard work is already sub-millisecond. "
        "I would still set up the cluster for the topology and failover "
        "demos, but I would not shard a 10K-document catalog in "
        "production.")
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
