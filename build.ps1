# Build script for SAM with optimizations
Write-Host "Cleaning previous build..." -ForegroundColor Yellow
Remove-Item -Recurse -Force .aws-sam -ErrorAction SilentlyContinue

Write-Host "`nBuilding SAM application..." -ForegroundColor Cyan
sam build --use-container

Write-Host "`nChecking build size..." -ForegroundColor Cyan
$layerSize = (Get-ChildItem -Recurse .aws-sam/build/OpenomiDependenciesLayer | Measure-Object -Property Length -Sum).Sum / 1MB
$functionSize = (Get-ChildItem -Recurse .aws-sam/build/OpenomiExtractionToolFunction | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Host "Layer size: $([math]::Round($layerSize, 2)) MB" -ForegroundColor Green
Write-Host "Function size: $([math]::Round($functionSize, 2)) MB" -ForegroundColor Green

if ($layerSize -gt 250) {
    Write-Host "`nWARNING: Layer size exceeds 250 MB limit!" -ForegroundColor Red
    Write-Host "Current size: $([math]::Round($layerSize, 2)) MB" -ForegroundColor Red
} else {
    Write-Host "`nBuild successful! Ready to deploy." -ForegroundColor Green
}
