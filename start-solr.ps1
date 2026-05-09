# Start Apache Solr in the foreground (Ctrl+C to stop).
# Solr listens on http://localhost:8983/solr
$ErrorActionPreference = 'Stop'
$bin = Join-Path $PSScriptRoot 'solr-9.6.1\bin\solr.cmd'
if (-not (Test-Path $bin)) { throw "Solr not found at $bin. Run extract-solr.ps1 first." }
& $bin start -f
