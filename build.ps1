$ErrorActionPreference = "Stop"

# Needed on Jenkins, somehow the env var PATH is not updated automatically
# after tool installations by scoop
Function ReloadEnvVars () {
    $Env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

Function ScoopInstall ([string[]]$Packages) {
    Invoke-CommandLine -CommandLine "scoop install $Packages"
    ReloadEnvVars
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

# Use default proxy
# $ProxyHost = '<your host>'
# $Env:HTTP_PROXY = "http://$ProxyHost"
# $Env:HTTPS_PROXY = $Env:HTTP_PROXY
# $Env:NO_PROXY = "localhost, .other-domain.com"
# $WebProxy = New-Object System.Net.WebProxy($Env:HTTP_PROXY, $true, ($Env:NO_PROXY).split(','))
# [net.webrequest]::defaultwebproxy = $WebProxy
# [net.webrequest]::defaultwebproxy.credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials

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
    
    ReloadEnvVars
}

# Necessary for 7zip installation, failed on Jenkins for unknown reason. See those issues:
# https://github.com/ScoopInstaller/Scoop/issues/460
# https://github.com/ScoopInstaller/Scoop/issues/4024
ScoopInstall('lessmsi')
Invoke-CommandLine -CommandLine "scoop config MSIEXTRACT_USE_LESSMSI $true"
# Default installer tools, e.g., dark is required for python
ScoopInstall('7zip', 'innounp', 'dark')
ScoopInstall('python')
Invoke-CommandLine -CommandLine "python -m pip install --quiet --trusted-host pypi.org --trusted-host files.pythonhosted.org python-certifi-win32"
Invoke-CommandLine -CommandLine "python -m pip install --upgrade pip"
Invoke-CommandLine -CommandLine "python -m pip install --quiet -r requirements.txt"

# We need GNU Make for transformation of Make projects
ScoopInstall('gcc')

if ($args) {
    Invoke-CommandLine -CommandLine "python src/transformer.py $args"
}
else {
    # Run test cases to be found in folder test/
    Invoke-CommandLine -CommandLine "python test/run_all.py" -StopAtError $false
}

$version=git rev-parse --short HEAD
Write-Host Transformer Version = $version