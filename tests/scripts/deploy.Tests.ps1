Describe "Hostel API deployment script" {
    $ScriptPath = Join-Path $PSScriptRoot "..\..\scripts\deploy.ps1"
    $ScriptPath = [System.IO.Path]::GetFullPath($ScriptPath)

    It "exists at the expected location" {
        Test-Path $ScriptPath | Should Be $true
    }

    It "requires an image tag parameter" {
        $Content = Get-Content $ScriptPath -Raw
        $Content | Should Match '\[string\]\$ImageTag'
        $Content | Should Match 'Mandatory\s*=\s*\$true'
    }

    It "updates the Kubernetes deployment image" {
        $Content = Get-Content $ScriptPath -Raw
        $Content | Should Match 'kubectl set image'
    }

    It "waits for the rollout to complete" {
        $Content = Get-Content $ScriptPath -Raw
        $Content | Should Match 'kubectl rollout status'
    }

    It "checks API, PostgreSQL, and Redis health" {
        $Content = Get-Content $ScriptPath -Raw
        $Content | Should Match 'Invoke-RestMethod'
        $Content | Should Match '\$Response\.postgres'
        $Content | Should Match '\$Response\.redis'
    }

    It "attempts a rollback when deployment verification fails" {
        $Content = Get-Content $ScriptPath -Raw
        $Content | Should Match 'kubectl rollout undo'
    }
}
