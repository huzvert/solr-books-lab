# Setup script: create the 'books' core, define schema, index the CSV.
# Usage:  .\setup.ps1
# Prereq: Solr running on localhost:8983 (run start-solr.ps1 first).

$ErrorActionPreference = 'Stop'
$Solr = 'http://localhost:8983/solr'
$Core = 'books'
$DataDir = Join-Path $PSScriptRoot 'data'
$SolrHome = Join-Path $PSScriptRoot 'solr-9.6.1\bin'

# 1. Create the core (idempotent — ignore if it already exists)
Write-Host "[1/3] Creating core '$Core'..." -ForegroundColor Cyan
& "$SolrHome\solr.cmd" create -c $Core 2>&1 | Out-Host

# 2. Define schema fields
Write-Host "[2/3] Defining schema fields..." -ForegroundColor Cyan
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
    Invoke-RestMethod -Method Post -Uri "$Solr/$Core/schema" `
      -ContentType 'application/json' -Body $body | Out-Null
    Write-Host "  + added $($f.name)" -ForegroundColor Green
  } catch {
    Write-Host "  ~ $($f.name) (already exists or skipped)" -ForegroundColor Yellow
  }
}

# 3. Index the CSV
Write-Host "[3/3] Indexing books.csv..." -ForegroundColor Cyan
$csv = Join-Path $DataDir 'books.csv'
$uri = "$Solr/$Core/update?commit=true&header=true"
Invoke-RestMethod -Method Post -Uri $uri `
  -ContentType 'application/csv; charset=utf-8' `
  -InFile $csv | Out-Null

# Verify
$res = Invoke-RestMethod "$Solr/$Core/select?q=*:*&rows=0"
Write-Host "Done. Indexed $($res.response.numFound) documents." -ForegroundColor Green
