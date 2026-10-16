param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$')]
    [string]$ImageTag,

    [string]$HealthUrl = "http://127.0.0.1:8080/health",

    [ValidateRange(30, 900)]
    [int]$RolloutTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

$Deployment = "hostel-api"
$Container = "api"
$Image = "darshan0369/hostel-allocation-python:$ImageTag"
$UpdateAttempted = $false

Write-Host "`n=== Hostel Allocation Deployment ===" -ForegroundColor Cyan
Write-Host "Target image: $Image"

# Verify Kubernetes connectivity before making any changes.
kubectl cluster-info
if ($LASTEXITCODE -ne 0) {
    throw "Cannot connect to Kubernetes. Deployment was not changed."
}

# Confirm the deployment exists and record its current image.
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

# Check that the health endpoint is reachable BEFORE changing the deployment.
try {
    $InitialHealth = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 5
    if (
        $InitialHealth.status -ne "ok" -or
        $InitialHealth.postgres -ne $true -or
        $InitialHealth.redis -ne $true
    ) {
        throw "Health endpoint is reachable but dependencies are not healthy."
    }
}
catch {
    throw "Pre-deployment health check failed at '$HealthUrl'. No image change was attempted. Ensure kubectl port-forward is running. Details: $($_.Exception.Message)"
}

try {
    Write-Host "`nUpdating deployment image..." -ForegroundColor Cyan

    # Mark the update as attempted so failures after this point trigger rollback.
    $UpdateAttempted = $true
    kubectl set image "deployment/$Deployment" "$Container=$Image"
    if ($LASTEXITCODE -ne 0) {
        throw "kubectl set image failed."
    }

    kubectl rollout status "deployment/$Deployment" "--timeout=${RolloutTimeoutSeconds}s"
    if ($LASTEXITCODE -ne 0) {
        throw "Kubernetes rollout failed or timed out."
    }

    Write-Host "`nVerifying application health..." -ForegroundColor Cyan
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

            Write-Host "Health check ${Attempt}: API or dependency is not healthy."
        }
        catch {
            Write-Host "Health check $Attempt failed; retrying..."
        }

        Start-Sleep -Seconds 5
    }

    if (-not $Healthy) {
        throw "Post-deployment health verification failed."
    }

    $DeployedImage = kubectl get deployment $Deployment `
        -o "jsonpath={.spec.template.spec.containers[?(@.name=='api')].image}"

    if ($LASTEXITCODE -ne 0 -or $DeployedImage -ne $Image) {
        throw "The deployment image does not match the requested image."
    }

    Write-Host "`nDeployment and health checks succeeded!" -ForegroundColor Green
    Write-Host "Running image: $DeployedImage" -ForegroundColor Green

    kubectl get deployment $Deployment -o wide
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read the final deployment status."
    }
}
catch {
    $FailureMessage = $_.Exception.Message

    Write-Host "`nDeployment failed: $FailureMessage" -ForegroundColor Red

    if ($UpdateAttempted) {
        Write-Host "Attempting rollback to the previous revision..." -ForegroundColor Yellow

        kubectl rollout undo "deployment/$Deployment"
        if ($LASTEXITCODE -ne 0) {
            throw "Rollback command failed. Inspect Kubernetes immediately. Original error: $FailureMessage"
        }

        kubectl rollout status "deployment/$Deployment" "--timeout=${RolloutTimeoutSeconds}s"
        if ($LASTEXITCODE -ne 0) {
            throw "Rollback rollout failed. Inspect Kubernetes immediately. Original error: $FailureMessage"
        }

        Write-Host "Rollback rollout completed. Previous image was: $PreviousImage" -ForegroundColor Yellow
    }

    throw $FailureMessage
}

