# PowerShell script to update all StarDate projects to .NET 8
# Run this script from the StarDate root directory

Write-Host "Updating all StarDate projects to .NET 8..." -ForegroundColor Green

# Function to update a project file
function Update-ProjectFile {
    param(
        [string]$ProjectPath,
        [string]$OldFramework,
        [string]$NewFramework,
        [bool]$IsExecutable = $false
    )
    
    if (Test-Path $ProjectPath) {
        Write-Host "Updating $ProjectPath..." -ForegroundColor Yellow
        
        $content = Get-Content $ProjectPath -Raw
        
        # Replace target framework
        $content = $content -replace "<TargetFramework>$OldFramework</TargetFramework>", "<TargetFramework>$NewFramework</TargetFramework>"
        
        # Add modern .NET properties after TargetFramework
        if ($content -notmatch "<LangVersion>") {
            $modernProps = @"
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
"@
            
            if ($IsExecutable) {
                $content = $content -replace "(<TargetFramework>$NewFramework</TargetFramework>)", "`$1`n$modernProps"
            } else {
                $content = $content -replace "(<TargetFramework>$NewFramework</TargetFramework>)", "`$1`n$modernProps"
            }
        }
        
        # Write back to file
        Set-Content $ProjectPath -Value $content -Encoding UTF8
        Write-Host "Updated $ProjectPath successfully!" -ForegroundColor Green
    } else {
        Write-Host "Project file not found: $ProjectPath" -ForegroundColor Red
    }
}

# Update all Blazor web apps
$blazorApps = @(
    "StarBlazeBrowser\StarBlazeBrowser.csproj",
    "NativeCalendar\NativeCalendar.csproj",
    "StarLib.Desktop\StarLib.Desktop.csproj"
)

foreach ($app in $blazorApps) {
    Update-ProjectFile -ProjectPath $app -OldFramework "netcoreapp3.1" -NewFramework "net8.0"
}

# Update console applications
$consoleApps = @(
    "StarLibDesktop\LazyDesktop.csproj"
)

foreach ($app in $consoleApps) {
    Update-ProjectFile -ProjectPath $app -OldFramework "netcoreapp3.1" -NewFramework "net8.0" -IsExecutable $true
}

# Update libraries that need multi-targeting
$libraries = @(
    "FamilyTerms\FamilyTerms.csproj",
    "Kinship\Kinship.csproj",
    "StarLib.Dynamic\StarLib.Dynamic.csproj",
    "StarLib.Calendar\StarLib.Calendar.csproj"
)

foreach ($lib in $libraries) {
    if (Test-Path $lib) {
        Write-Host "Updating $lib for multi-targeting..." -ForegroundColor Yellow
        
        $content = Get-Content $lib -Raw
        
        # Replace with multi-targeting
        $content = $content -replace "<TargetFramework>netstandard2\.0</TargetFramework>", "<TargetFrameworks>net8.0;netstandard2.0</TargetFrameworks>"
        $content = $content -replace "<TargetFramework>netcoreapp3\.1</TargetFramework>", "<TargetFrameworks>net8.0;netstandard2.0</TargetFrameworks>"
        
        # Add modern properties if not present
        if ($content -notmatch "<LangVersion>") {
            $modernProps = @"
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
"@
            $content = $content -replace "(<TargetFrameworks>[^<]+</TargetFrameworks>)", "`$1`n$modernProps"
        }
        
        Set-Content $lib -Value $content -Encoding UTF8
        Write-Host "Updated $lib successfully!" -ForegroundColor Green
    }
}

Write-Host "`nAll projects updated to .NET 8!" -ForegroundColor Green
Write-Host "Run 'dotnet build' to verify the updates." -ForegroundColor Cyan