#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Execute Fase 1 vs Fase 2 comparison with proper UTF-8 encoding on Windows.

.DESCRIPTION
    Runs the main_comparison.py script with UTF-8 encoding to avoid 
    console encoding errors on Windows systems.

.EXAMPLE
    .\run_comparison.ps1 --rules SPT,EDD --dataset "TA:datasets/jobshop1.txt:1"
#>

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'

# Set UTF-8 encoding
$env:PYTHONIOENCODING = 'utf-8'

# Change to script directory
Push-Location $PSScriptRoot

try {
    # Run main_comparison
    python -m twin_scheduler_simpy.main_comparison @Arguments
}
finally {
    Pop-Location
}
