<#
.DESCRIPTION
    Wrapper for installing dependencies, running and testing the project

.Notes
On Windows, it may be required to call this script with the proper execution policy.
You can do this by issuing the following PowerShell command:

PS C:\> powershell -ExecutionPolicy Bypass -File .\build.ps1

For more information on Execution Policies:
https://go.microsoft.com/fwlink/?LinkID=135170
#>

param(
    [switch]$clean ## clean build, wipe out all build artifacts
    , [switch]$install ## install mandatory packages
)

Function Invoke-CommandLine {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingInvokeExpression', '', Justification = 'Usually this statement must be avoided (https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/avoid-using-invoke-expression?view=powershell-7.3), here it is OK as it does not execute unknown code.')]
    param (
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$CommandLine,
        [Parameter(Mandatory = $false, Position = 1)]
        [bool]$StopAtError = $true,
        [Parameter(Mandatory = $false, Position = 2)]
        [bool]$Silent = $false
    )
    if (-Not $Silent) {
        Write-Output "Executing: $CommandLine"
    }
    $global:LASTEXITCODE = 0
    Invoke-Expression $CommandLine
    if ($global:LASTEXITCODE -ne 0) {
        if ($StopAtError) {
            Write-Error "Command line call `"$CommandLine`" failed with exit code $global:LASTEXITCODE"
        }
        else {
            if (-Not $Silent) {
                Write-Output "Command line call `"$CommandLine`" failed with exit code $global:LASTEXITCODE, continuing ..."
            }
        }
    }
}

Function Import-Dot-Env {
    if (Test-Path -Path '.env') {
        # load environment properties
        $envProps = ConvertFrom-StringData (Get-Content '.env' -raw)
    }

    Return $envProps
}

Function Initialize-Proxy {
    $envProps = Import-Dot-Env
    if ($envProps.'HTTP_PROXY') {
        $Env:HTTP_PROXY = $envProps.'HTTP_PROXY'
        $Env:HTTPS_PROXY = $Env:HTTP_PROXY
        if ($envProps.'NO_PROXY') {
            $Env:NO_PROXY = $envProps.'NO_PROXY'
            $WebProxy = New-Object System.Net.WebProxy($Env:HTTP_PROXY, $true, ($Env:NO_PROXY).split(','))
        }
        else {
            $WebProxy = New-Object System.Net.WebProxy($Env:HTTP_PROXY, $true)
        }

        [net.webrequest]::defaultwebproxy = $WebProxy
        [net.webrequest]::defaultwebproxy.credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
    }
}


## start of script
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
Write-Output "Running in ${pwd}"

Initialize-Proxy

if ($install) {
    if (-Not (Test-Path -Path '.bootstrap')) {
        New-Item -ItemType Directory '.bootstrap'
    }
    # Installation of Scoop, Python and pipenv via bootstrap
    $bootstrapSource = 'https://raw.githubusercontent.com/avengineers/bootstrap/develop/bootstrap.ps1'
    Invoke-RestMethod $bootstrapSource -OutFile '.\.bootstrap\bootstrap.ps1'
    Invoke-CommandLine '. .\.bootstrap\bootstrap.ps1'
    Write-Output "For installation changes to take effect, please close and re-open your current shell."
}
else {
    # To avoid Jenkins reboot force a reload of environment after installation
    if ($Env:JENKINS_URL -and $Env:BUILD_NUMBER) {
        $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }

    if ($clean) {
        # Remove all build artifacts
        $buildDirs = '.\output'
        foreach ($buildDir in $buildDirs) {
            if (Test-Path -Path $buildDir) {
                Remove-Item $buildDir -Force -Recurse
            }
        }
    }
    if ($args) {
        Invoke-CommandLine -CommandLine "python -m pipenv run python src/transformer.py $args"
        $version=git rev-parse --short HEAD
        Write-Host Transformer Version = $version
    }
    else {
        # Run test cases to be found in folder test/
        Invoke-CommandLine -CommandLine "python -m pipenv run pytest" -StopAtError $false
    }
}

Pop-Location
## end of script
