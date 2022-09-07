$ErrorActionPreference = "Stop"

# Needed on Jenkins, somehow the env var PATH is not updated automatically
# after tool installations by scoop
Function ReloadEnvVars () {
    $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
}

Function ScoopInstall ([string[]]$Packages) {
    if ($Packages) {
        Invoke-CommandLine -CommandLine "scoop install $Packages"
        ReloadEnvVars
    }
}

Function PythonInstall ([string[]]$Packages) {
    if ($Packages) {
        $PipInstaller = "python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org"
        Invoke-CommandLine -CommandLine "$PipInstaller $Packages"
        ReloadEnvVars
    }
}

Function Invoke-CommandLine {
    param (
        [string]$CommandLine,
        [bool]$StopAtError = $true
    )
    Write-Host "Executing: $CommandLine"
    Invoke-Expression $CommandLine
    if ($LASTEXITCODE -ne 0) {
        if ($StopAtError) {
            throw "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE"
        }
        else {
            Write-Host "Command line call `"$CommandLine`" failed with exit code $LASTEXITCODE, continuing ..."
        }
    }
}

Push-Location $PSScriptRoot

# TODO: read proxy from a configuration file to make this script independent on network settings
if ($Env:HTTP_PROXY -and $Env:HTTPS_PROXY -and $Env:NO_PROXY) {
    $WebProxy = New-Object System.Net.WebProxy($Env:HTTP_PROXY, $true, ($Env:NO_PROXY).split(','))
    [net.webrequest]::defaultwebproxy = $WebProxy
    [net.webrequest]::defaultwebproxy.credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
}

# Initial Scoop installation
ReloadEnvVars
if (-Not (Get-Command scoop -errorAction SilentlyContinue)) {
    # Initial Scoop installation
    iwr get.scoop.sh -outfile 'install.ps1'
    if ((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        & .\install.ps1 -RunAsAdmin
    } else {
        & .\install.ps1
    }
    ReloadEnvVars
}

Write-Output "Running in ${pwd}"

# Necessary for 7zip installation, failed on Jenkins for unknown reason. See those issues:
# https://github.com/ScoopInstaller/Scoop/issues/460
# https://github.com/ScoopInstaller/Scoop/issues/4024
ScoopInstall('lessmsi')
Invoke-CommandLine -CommandLine "scoop config MSIEXTRACT_USE_LESSMSI $true"
# Default installer tools, e.g., dark is required for python
ScoopInstall('7zip', 'innounp', 'dark')
Invoke-CommandLine -CommandLine "scoop bucket add versions" -StopAtError $false -Silent $true
Invoke-CommandLine -CommandLine "scoop update"
ScoopInstall('python')
[string[]]$packages = Get-Content -Path .\requirements.txt
PythonInstall($packages)

# We need GNU Make for transformation of Make projects
ScoopInstall('mingw-winlibs-llvm-ucrt')

if ($args) {
    Invoke-CommandLine -CommandLine "python src/transformer.py $args"
}
else {
    # Run test cases to be found in folder test/
    Invoke-CommandLine -CommandLine "python test/run_all.py" -StopAtError $false
}

$version=git rev-parse --short HEAD
Write-Host Transformer Version = $version

Pop-Location