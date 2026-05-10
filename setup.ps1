# End-to-end setup: create sharded 'books' collection, define schema, index data.
# Prereq: SolrCloud running on localhost:8983 (start with .\start-solr.ps1).
# Optional: Real dataset in data\books.csv. If missing, run:
#   python data\transform_goodbooks.py   (after downloading goodbooks_raw.csv)

$ErrorActionPreference = 'Continue'
$Solr = 'http://localhost:8983/solr'
$Col  = 'books'
$DataDir = Join-Path $PSScriptRoot 'data'

# 1. Create the collection (2 shards, 2 replicas) — idempotent
Write-Host "[1/4] Creating collection '$Col' (numShards=2, replicationFactor=2)..." -ForegroundColor Cyan
try {
  Invoke-RestMethod "$Solr/admin/collections?action=CREATE&name=$Col&numShards=2&replicationFactor=2&collection.configName=_default" | Out-Null
  Write-Host "  created" -ForegroundColor Green
} catch {
  Write-Host "  collection already exists (skip)" -ForegroundColor Yellow
}
Start-Sleep -Seconds 3

# 2. Define schema fields
Write-Host "[2/4] Defining schema fields..." -ForegroundColor Cyan
$fields = @(
  @{name='title';       type='text_general'; stored=$true; indexed=$true},
  @{name='author';      type='text_general'; stored=$true; indexed=$true},
  @{name='genre';       type='string';       stored=$true; indexed=$true},
  @{name='publisher';   type='string';       stored=$true; indexed=$true},
  @{name='year';        type='pint';         stored=$true; indexed=$true},
  @{name='pages';       type='pint';         stored=$true; indexed=$true},
  @{name='price';       type='pfloat';       stored=$true; indexed=$true},
  @{name='rating';      type='pfloat';       stored=$true; indexed=$true},
  @{name='in_stock';    type='boolean';      stored=$true; indexed=$true},
  @{name='description'; type='text_general'; stored=$true; indexed=$true}
)
foreach ($f in $fields) {
  $body = @{ 'add-field' = $f } | ConvertTo-Json -Compress
  try {
    Invoke-RestMethod -Method Post -Uri "$Solr/$Col/schema" -ContentType 'application/json' -Body $body | Out-Null
    Write-Host "  + $($f.name)" -ForegroundColor Green
  } catch {
    Write-Host "  ~ $($f.name) (already defined)" -ForegroundColor Yellow
  }
}

# 3. Index the CSV
$csv = Join-Path $DataDir 'books.csv'
if (-not (Test-Path $csv)) { throw "data\books.csv not found. Run: python data\transform_goodbooks.py" }
Write-Host "[3/4] Indexing $csv..." -ForegroundColor Cyan
$t0 = Get-Date
Invoke-RestMethod -Method Post -Uri "$Solr/$Col/update?commit=true&header=true" `
  -ContentType 'application/csv; charset=utf-8' -InFile $csv | Out-Null
$dt = ((Get-Date) - $t0).TotalSeconds
Write-Host "  indexed in $($dt.ToString('F1'))s" -ForegroundColor Green

# 4. Verify
Write-Host "[4/4] Verifying..." -ForegroundColor Cyan
$res = Invoke-RestMethod "$Solr/$Col/select?q=*:*&rows=0"
Write-Host "  total docs across both shards: $($res.response.numFound)" -ForegroundColor Green

Write-Host ""
Write-Host "Done. Open http://localhost:8983/solr/ to inspect, or run python app\app.py for the UI." -ForegroundColor Cyan
