# Start a 2-node SolrCloud cluster (ports 8983, 7574; ZK on 9983).
# Stop with .\stop-solr.ps1
$ErrorActionPreference = 'Stop'
$bin = Join-Path $PSScriptRoot 'solr-9.6.1\bin\solr.cmd'
if (-not (Test-Path $bin)) { throw "Solr not found at $bin. Run extract-solr.ps1 first." }
& $bin -e cloud -noprompt
