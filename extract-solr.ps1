# Extract solr-9.6.1.tgz into the project directory.
$ErrorActionPreference = 'Stop'
$tgz = Join-Path $PSScriptRoot '..\solr-9.6.1.tgz'
if (-not (Test-Path $tgz)) {
  $tgz = Join-Path $PSScriptRoot 'solr-9.6.1.tgz'
}
if (-not (Test-Path $tgz)) {
  throw "solr-9.6.1.tgz not found. Download from https://archive.apache.org/dist/solr/solr/9.6.1/"
}
Write-Host "Extracting $tgz ..." -ForegroundColor Cyan
tar -xzf $tgz -C $PSScriptRoot
Write-Host "Done. Solr at $(Join-Path $PSScriptRoot 'solr-9.6.1')" -ForegroundColor Green
