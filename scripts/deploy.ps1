param(
    [Parameter(Mandatory = $true)]
    [string]$ImageTag,

    [string]$HealthUrl = "http://127.0.0.1:8080/health",

    [int]$RolloutTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

$Deployment = "hostel-api"
$Container = "api"
$Image = "darshan0369/hostel-allocation-python:$ImageTag"

Write-Host "`n=== Hostel Allocation Deployment ===" -ForegroundColor Cyan
Write-Host "Target image: $Image"

kubectl cluster-info
if ($LASTEXITCODE -ne 0) {
    throw "Cannot connect to Kubernetes."
}

$PreviousImage = kubectl get deployment $Deployment `
    -o "jsonpath={.spec.template.spec.containers[?(@.name=='api')].image}"

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PreviousImage)) {
    throw "Could not read the current deployment image."
}

Write-Host "Current image: $PreviousImage"

if ($PreviousImage -eq $Image) {
    Write-Host "The requested image is already deployed." -ForegroundColor Green
    exit 0
}

try {
    kubectl set image "deployment/$Deployment" "$Container=$Image"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update the image."
    }

    kubectl rollout status "deployment/$Deployment" "--timeout=${RolloutTimeoutSeconds}s"
    if ($LASTEXITCODE -ne 0) {
        throw "Kubernetes rollout failed."
    }

    $Healthy = $false

    for ($Attempt = 1; $Attempt -le 12; $Attempt++) {
        try {
            $Response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 5

            if (
                $Response.status -eq "ok" -and
                $Response.postgres -eq $true -and
                $Response.redis -eq $true
            ) {
                $Healthy = $true
                break
            }
        }
        catch {
            Write-Host "Health check attempt $Attempt failed."
        }

        Start-Sleep -Seconds 5
    }

    if (-not $Healthy) {
        throw "API health check failed."
    }

    Write-Host "Deployment and health checks succeeded!" -ForegroundColor Green
    kubectl get deployment $Deployment -o wide
}
catch {
    $FailureMessage = $_.Exception.Message

    Write-Host "Deployment failed: $FailureMessage" -ForegroundColor Red
    Write-Host "Rolling back..." -ForegroundColor Yellow

    kubectl rollout undo "deployment/$Deployment"
    if ($LASTEXITCODE -ne 0) {
        throw "Rollback command failed. Inspect Kubernetes immediately."
    }

    kubectl rollout status "deployment/$Deployment" "--timeout=${RolloutTimeoutSeconds}s"
    if ($LASTEXITCODE -ne 0) {
        throw "Rollback rollout failed. Inspect Kubernetes immediately."
    }

    throw $FailureMessage
}
