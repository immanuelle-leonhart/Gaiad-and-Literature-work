# StarDate .NET Upgrade Guide

## Overview

This guide helps you upgrade the StarDate Cosmic Calendar project from legacy .NET Framework/Core to modern .NET 8.

## What Changed

### Framework Upgrades
- **StarLib**: `netstandard1.6` → `net8.0` + `netstandard2.0` (multi-targeting)
- **StarLib.Forms**: `netstandard2.0` + Blazor 3.1 → `net8.0` + Blazor 8.0
- **Applications**: `netcoreapp3.1` → `net8.0`

### New Features in Version 2.0
- **ISO Week Alignment**: 1宮1日 (Sagittarius 1) = ISO Week 1, Day 1
- **Modern .NET 8**: Latest C# features, nullable reference types, implicit usings
- **Improved Performance**: Modern runtime optimizations
- **Better Blazor**: Latest Blazor 8.0 components with enhanced interactivity

## Migration Steps

### 1. Prerequisites
```bash
# Install .NET 8 SDK
winget install Microsoft.DotNet.SDK.8
# OR download from: https://dotnet.microsoft.com/download/dotnet/8.0
```

### 2. Update Project Files
All project files have been modernized with:
- Target framework upgrades
- Modern package references
- Nullable reference types enabled
- Implicit usings enabled
- Latest language version

### 3. Code Changes Required

#### Nullable Reference Types
With `<Nullable>enable</Nullable>`, you may need to:

```csharp
// Old code
string name = GetName();

// Modern code with null safety
string? name = GetName(); // If can be null
string name = GetName() ?? throw new InvalidOperationException("Name cannot be null");
```

#### Implicit Usings
Common `using` statements are now global (see `GlobalUsings.cs`):
- No need to import `System`, `System.Collections.Generic`, etc.
- Custom using statements still needed for specialized namespaces

#### System.Text.Json Support
Added alongside Newtonsoft.Json for modern serialization:

```csharp
// New option: System.Text.Json
using System.Text.Json;
var json = JsonSerializer.Serialize(starDate);

// Still supported: Newtonsoft.Json
using Newtonsoft.Json;
var json = JsonConvert.SerializeObject(starDate);
```

### 4. Blazor Updates

#### Modern Component Syntax
```razor
@* Old Blazor 3.1 *@
@using Microsoft.AspNetCore.Components

@* New Blazor 8.0 - implicit usings *@
@* Using statements are now global *@
```

#### Enhanced Interactivity
```razor
@* New interactive rendering modes *@
@rendermode InteractiveServer
@rendermode InteractiveWebAssembly
@rendermode InteractiveAuto
```

### 5. Package Updates

#### Removed Packages (now in framework)
- `Microsoft.Win32.Primitives`
- `System.Runtime`
- `System.Runtime.InteropServices`
- `Microsoft.PowerShell.5.ReferenceAssemblies` (removed from Blazor)

#### Updated Packages
- `Newtonsoft.Json`: `12.0.3` → `13.0.3`
- `Microsoft.AspNetCore.Components`: `3.1.6` → `8.0.8`
- `System.Runtime.CompilerServices.Unsafe`: `4.7.1` → `6.0.0`

#### New Packages
- `System.Text.Json`: `8.0.4` (modern JSON serialization)

## Breaking Changes

### API Changes
The ISO Week alignment introduces new properties:
- `Palace`: Chinese/Japanese palace number (1宮-14宮)
- `IsoDayOfWeek`: ISO day of week (1=Monday, 7=Sunday)
- `WeekOfYear`: Now returns ISO week numbers (1-53)

### Behavioral Changes
- **1宮1日 always = Monday**: Previously could fall on any day of week
- **Horus week = ISO Week 53**: No longer inserted between months
- **Fixed scheduling**: All dates now have consistent weekdays

## Build and Test

### Command Line Build
```bash
# Build the solution
dotnet build StarDate.sln

# Run tests
dotnet test

# Create packages
dotnet pack
```

### Visual Studio
- Requires **Visual Studio 2022 17.8+** for full .NET 8 support
- Blazor projects require **ASP.NET and web development** workload

## Compatibility

### Backwards Compatibility
- **API**: Most existing APIs remain unchanged
- **Serialization**: JSON and XML serialization preserved
- **Interop**: DateTime conversions still work

### Multi-Targeting
StarLib targets both:
- `net8.0`: For modern applications with latest features
- `netstandard2.0`: For compatibility with older .NET Framework 4.6.1+

## Performance Improvements

### .NET 8 Benefits
- **Faster startup**: 15-30% improvement in application start time
- **Memory usage**: Reduced memory allocation and GC pressure
- **JSON**: System.Text.Json is 2-3x faster than Newtonsoft.Json
- **Blazor**: Improved rendering performance and smaller bundle sizes

### ISO Week Calculations
The new week calculation algorithm is more efficient:
```csharp
// Old: Day-based calculation
int weekNum = ((DayOfYear - 1) / 7) + 1;

// New: Month-based calculation (faster)
int weekNum = ((Month - 1) * 4) + ((Day - 1) / 7) + 1;
```

## Deployment

### Self-Contained Deployment
```bash
# Create self-contained executable
dotnet publish -c Release -r win-x64 --self-contained true

# Create framework-dependent deployment
dotnet publish -c Release
```

### NuGet Package
Updated packages will be published as:
- `StarDate` version 2.0.0 (core library)
- `StarDate.Forms` version 2.0.0 (Blazor components)

## Troubleshooting

### Common Issues

#### Nullable Reference Warnings
```csharp
// If you get CS8618 warnings
#nullable disable
// Your legacy code here
#nullable restore
```

#### Missing Using Statements
Add to GlobalUsings.cs:
```csharp
global using YourNamespace;
```

#### Blazor Routing Issues
Update routing in Program.cs:
```csharp
// .NET 8 style
app.MapRazorComponents<App>()
   .AddInteractiveServerRenderMode()
   .AddInteractiveWebAssemblyRenderMode();
```

### Getting Help
- Check GitHub Issues: https://github.com/siliconprophet/StarDate/issues
- .NET 8 Migration Guide: https://docs.microsoft.com/en-us/dotnet/core/compatibility/
- Blazor 8.0 Guide: https://docs.microsoft.com/en-us/aspnet/core/blazor/

## What's Next

### Future Enhancements
- **AOT Compilation**: Native ahead-of-time compilation support
- **Minimal APIs**: Lightweight HTTP API endpoints
- **Cloud Native**: Container and Kubernetes optimizations
- **MAUI Support**: Cross-platform mobile and desktop applications

The StarDate Cosmic Calendar is now ready for the modern .NET ecosystem while maintaining its cosmic and mythological foundations!