$ErrorActionPreference = 'Stop'
$bin = Join-Path $PSScriptRoot 'solr-9.6.1\bin\solr.cmd'
& $bin stop -all
