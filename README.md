# Apache Solr — Books Search Lab (CS-347 Lab 13)

End-to-end Apache Solr lab: indexing, querying and a Flask web UI for searching a books catalog.

## Stack
- Apache Solr 9.6.1 (standalone)
- Python 3.13 + Flask + requests
- Vanilla HTML/CSS/JS frontend (no build step)

## Project layout
```
solr-search-app/
+- data/
|  +- generate_books.py     # synthesizes books.csv (600 records)
|  +- books.csv             # generated dataset
|  +- schema_setup.json     # field type definitions (reference)
+- app/
|  +- app.py                # Flask backend
|  +- templates/index.html  # search UI
|  +- static/styles.css
+- solr-9.6.1/              # Solr install (created by extract-solr.ps1)
+- start-solr.ps1           # solr start -f
+- stop-solr.ps1            # solr stop -all
+- setup.ps1                # creates core, defines schema, indexes data
+- sample_queries.md        # 12 sample queries with explanations
+- requirements.txt
```

## Setup (Windows)

### 1. Install Solr
Download `solr-9.6.1.tgz` from https://archive.apache.org/dist/solr/solr/9.6.1/
and extract into this directory:
```powershell
tar -xzf solr-9.6.1.tgz
```

### 2. Start Solr
```powershell
.\start-solr.ps1
```
Wait for `Started Solr server on port 8983`. Confirm at http://localhost:8983/solr/

### 3. Create core, define schema, index data (in a new terminal)
```powershell
python data\generate_books.py     # creates books.csv (skip if already present)
.\setup.ps1
```
You should see `Done. Indexed 600 documents.`

### 4. Run the web app
```powershell
pip install -r requirements.txt
python app\app.py
```
Open http://localhost:5000

## Features implemented

| Feature                      | Where                                    |
| ---------------------------- | ---------------------------------------- |
| Full-text search (edismax)   | `app.py: solr_search()`                  |
| Faceted navigation           | sidebar — genre, publisher, in_stock     |
| Range filter                 | year from/to in sidebar                  |
| Sorting                      | dropdown — relevance, year, price, rating |
| Pagination                   | bottom of results page                   |
| Highlighting                 | `<mark>` tags on title/author/description |
| Autocomplete                 | `/suggest` endpoint, 150 ms debounce     |
| Responsive UI                | media query at 800 px                    |

## Sample queries
See `sample_queries.md` for 12 worked examples (filtering, faceting, range
facets, fuzzy search, function-query boosts, grouping).

## License
MIT — academic submission for CS-347 Lab 13.
