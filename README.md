# Apache Solr — Product Search Lab (CS-347 Lab 13)

End-to-end Apache Solr lab: a 2-node sharded SolrCloud cluster indexing 996 real
Amazon products, with a Flask web UI on top. Every searchable field comes from
the source dataset — no synthetic columns.

## Stack
- Apache Solr 9.6.1 in **SolrCloud** mode (2 nodes on 8983/7574, embedded ZooKeeper on 9983)
- 3,202-record real e-commerce dataset combining 4 marketplaces (Amazon, Walmart, Lazada, Shopee)
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

### 2. Start the SolrCloud cluster
```powershell
.\start-solr.ps1
```
This calls `solr.cmd -e cloud -noprompt` and brings up two nodes (8983, 7574)
with embedded ZooKeeper on 9983. Confirm at http://localhost:8983/solr/

### 3. Get the datasets
```powershell
curl -L -o data\amazon_raw.csv      https://raw.githubusercontent.com/luminati-io/Amazon-dataset-samples/main/amazon-products.csv
curl -L -o data\walmart-products.csv https://raw.githubusercontent.com/luminati-io/eCommerce-dataset-samples/main/walmart-products.csv
curl -L -o data\lazada-products.csv  https://raw.githubusercontent.com/luminati-io/eCommerce-dataset-samples/main/lazada-products.csv
curl -L -o data\shopee-products.csv  https://raw.githubusercontent.com/luminati-io/eCommerce-dataset-samples/main/shopee-products.csv
python data\transform_ecommerce.py
```
This produces `data\products.csv` with 3,202 records across 4 marketplaces.

### 4. Create the sharded collection, define schema, index data
```powershell
.\setup.ps1
```
You should see `total docs across both shards: 3202`.

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
