# StarDate C# Project Documentation

## Overview

The StarDate C# project implements the **Gaian Cosmic Calendar**, also known as the **Celestial Calendar**. This is a comprehensive calendar system designed for both current Earth-based timekeeping and future space-based civilizations. The project provides a complete replacement for .NET's DateTime system with cosmic and mythological foundations.

## Core Concept

The Celestial Calendar is a **sidereal leap week calendar** that tracks time from an estimated date of the Big Bang (~14 billion years ago) and uses astronomical rather than seasonal markers for its year boundaries.

### Key Features

- **Sidereal-based**: New year begins when Earth crosses between Sagittarius A* (galactic center, called "Chiron" in the Gaiad mythology) and the Sun
- **13-month system**: Based on the 13-sign zodiac (12 classical signs plus Ophiuchus)
- **ISO Week Compliance**: **1宮1日 (Sagittarius 1)** always aligns with **ISO Week 1, Day 1** (Monday)
- **Fixed weekday system**: Each month has exactly 28 days (4 weeks), ensuring consistent scheduling
- **Leap week system**: Intercalary weeks are designated as **ISO Week 53** (Horus week)
- **Palace numbering**: Chinese/Japanese month system using 宮 (palace) numbers: 1宮-14宮
- **Cosmic timescale**: Supports both "short dates" (from agriculture ~12,000 years ago) and "long dates" (from Big Bang)

## Project Structure

### Core Libraries

#### **StarLib** (Main Library)
- **StarDate.cs**: Core date/time structure, equivalent to .NET's DateTime
- **StarCulture.cs**: Localization and formatting support for different languages
- **StarZone.cs**: Time zone handling for Earth, Mars, and space travel
- **Time.cs**: Alternative to TimeSpan for cosmic durations
- **StarDateFormat.cs**: Comprehensive formatting system
- **StarDateParse.cs**: String parsing functionality

#### **StarLib.Forms** (UI Components)
- **InputStarDate.razor**: Blazor component for date input
- **Calendar14.razor**, **Calendar28.razor**, **Calendar7.razor**: Different calendar view components
- **Converter.razor**: Date conversion between Gregorian and Celestial calendars

#### **StarLib.Calendar** (Calendar Export)
- **Ical.cs**: iCal format export functionality for calendar applications

### Applications and Demos

#### **Web Applications**
- **BlazorDemonstration**: Basic Blazor web demo
- **CalendarConverter**: Web-based calendar conversion tool
- **NativeCalendar**: Native calendar implementation
- **StarBlazeBrowser**: Enhanced Blazor browser application

#### **Desktop Applications**
- **BlazorDesktopApp**: Desktop version using Blazor WebView
- **StarLib.Desktop**: Full desktop calendar application
- **StarLibDesktop**: Streamlined desktop version

#### **Console Applications**
- **TestConsole**: Testing and validation console app
- **ConsoleApp1**: Basic console implementation
- **HelloWorldApp**: Simple demonstration

### Supporting Libraries

#### **Additional Components**
- **FamilyTerms**: Kinship and family relationship calculations
- **Kinship**: Extended family relationship modeling
- **StarLib.Dynamic**: Dynamic language binding support

## Calendar System Details

### Month Structure
- **13 months** per year, each with **28 days** (4 weeks)
- **364 days** in a regular year
- **Month names**: Based on zodiac signs (Sagittarius, Capricorn, Aquarius, Pisces, Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Ophiuchus)
- **ISO Week Alignment**: **1宮1日 (Sagittarius 1)** always falls on **ISO Week 1, Day 1** (Monday)
- **Palace System**: Months are numbered as 宮 (palaces) in Chinese/Japanese: 1宮 = Sagittarius, 2宮 = Capricorn, etc.

### Leap System
- **Every 6th year**: Adds one leap week (**Horus week** = **ISO Week 53**)
- **Every 78th year**: Adds two leap weeks (14 days total)
- **Maximum year length**: 378 days
- **Intercalary week placement**: Horus week is designated as ISO Week 53, not inserted between months

### ISO Week Alignment System

#### Core Principle
The calendar system has been modified to ensure **1宮1日 (Sagittarius 1)** always corresponds to **ISO Week 1, Day 1** (Monday). This creates perfect alignment between the cosmic calendar and international business/scheduling standards.

#### Week Structure
- **Regular months**: Each month contains exactly 4 weeks (weeks 1-52 distributed across months 1-13)
- **Intercalary weeks**: Horus leap weeks are designated as **ISO Week 53**
- **Day numbering**: Day 1 of every month = Monday, Day 2 = Tuesday, etc.
- **Palace system**: 1宮1日 = "1st Palace, 1st Day" = Sagittarius 1st = ISO Week 1, Monday

#### Benefits
- **International compatibility**: Seamless integration with ISO 8601 business calendar systems
- **Fixed scheduling**: Holidays and events always fall on the same day of the week
- **Business alignment**: Week numbers correspond directly to international standards
- **Cosmic significance**: Maintains astronomical anchoring while supporting practical usage

### Year Numbering Systems

#### Short Dates
- **Year 1**: Roughly corresponds to when Göbekli Tepe was built (~10,000 BCE)
- **Current year**: 2024 CE = 12024 AM (Anno Manu)
- **Prefix**: "1" added before Gregorian year (2020 → 12020)

#### Long Dates  
- **Year 1**: Estimated Big Bang (~14 billion years ago)
- **Current year**: ~14,000,012,024 years since Big Bang
- **Usage**: For cosmic-scale calculations and space travel

### Time Zones and Space Features

#### Earth Time Zones
- Standard Earth time zone support
- Daylight saving time compatibility
- Legacy DateTime interoperability

#### Space Features (In Development)
- **Mars support**: Martian days (~24 hours 30 minutes)
- **Lunar cycles**: Support for major moons in the solar system
- **Interstellar time**: Accounts for light-speed communication delays
- **Relativistic effects**: Time dilation calculations for space travel

## Technical Implementation

### Core Data Types

#### StarDate Structure
```csharp
// Core constructor
new StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks)

// With timezone and error margin
new StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks, StarZone timezone, TimeSpan error)

// From Gregorian conversion
StarDate(DateTime dt)
StarDate.FromGreg(year, month, day, hour, minute, second)
```

#### Key Properties
- **Ticks**: 100-nanosecond intervals since Big Bang (BigInteger)
- **Year/Month/Day**: Standard calendar components
- **Palace**: Chinese/Japanese palace number (1宮-14宮)
- **WeekOfYear**: ISO week number (1-53, where 53 = Horus intercalary week)
- **IsoDayOfWeek**: ISO day of week (1=Monday, 7=Sunday)
- **TimeZone**: StarZone object for location-specific time
- **Error**: Margin of error for astronomical calculations
- **MonthName/MonthSymbol**: Localized month names and zodiac symbols

### Formatting System

#### Custom Format Patterns
- **Date components**: `d`, `dd`, `M`, `MM`, `MMM`, `MMMM`, `y`, `yy`, `yyyy`
- **Time components**: `h`, `hh`, `H`, `HH`, `m`, `mm`, `s`, `ss`, `f-fffffff`
- **Cosmic elements**: `b` (billions/millions), `W` (weekday symbols), `MMM` (zodiac symbols)
- **Zone information**: `z`, `zz`, `zzz`, `zzzz` (time zone offsets and names)

#### Standard Format Strings
- **"d"**: Short date (10/28/11999)
- **"D"**: Long date (Sunday, Virgo 28, 11999)
- **"f"/"F"**: Full date and time combinations
- **"o"/"O"**: Round-trip XML format
- **"r"/"R"**: RFC 1123 format

### Conversion and Interoperability

#### Gregorian Calendar Integration
- **Automatic conversion**: Implicit casting between DateTime and StarDate
- **Accuracy**: Accounts for Gregorian calendar irregularities
- **Performance**: Optimized tick-based conversion where possible

#### Export Formats
- **iCal**: Standard calendar format for integration with existing calendar applications
- **CSV**: Date conversion charts for analysis
- **XML**: Serialization support

## Mythological Context

### Cultural Foundation
The calendar is based on the **Gaiad** mythology, a cosmological creation story that provides cultural context for the technical implementation:

- **Manu**: Mythological first human, born at midnight on Sagittarius 1st, Year 1
- **Galactic alignment**: New year determined by Earth's position relative to galactic center
- **Zodiac integration**: Months named after constellation positions
- **Era naming**: "Anno Manu" (A.M.) instead of Anno Domini

### Astronomical Basis
- **Precession awareness**: Calendar accounts for Earth's axial wobble over 26,000-year cycles
- **Stellar focus**: Prioritizes star positions over seasonal changes
- **Long-term stability**: Designed for space-faring civilization timeline

## Applications and Use Cases

### Current Applications
- **Academic research**: Calendar system studies and historical date conversion
- **Cultural projects**: Integration with mythological and literary works
- **Software development**: Alternative calendar system for applications

### Future Vision
- **Space colonization**: Time synchronization across solar system
- **Interstellar travel**: Communication delay and relativistic effect handling
- **Long-term planning**: Cosmic-scale project management and historical record-keeping

## Development Tools

### Web Interfaces
- **Calendar converters**: Gregorian ↔ Celestial date conversion
- **Visual calendars**: Interactive calendar displays
- **Date selectors**: Form components for web applications

### Desktop Tools
- **Calendar applications**: Full-featured desktop calendar software
- **Conversion utilities**: Batch date conversion tools
- **Testing frameworks**: Validation and accuracy testing

### Integration Support
- **.NET compatibility**: Drop-in replacement for DateTime in many scenarios
- **JSON serialization**: Web API and data storage support
- **Localization**: Multi-language month and day names

## Project Status

### Completed Features
- ✅ Core calendar mathematics and date calculations
- ✅ Gregorian calendar conversion
- ✅ Basic time zone support
- ✅ Formatting and parsing system
- ✅ Web and desktop demonstration applications
- ✅ Blazor UI components

### In Development
- 🚧 Mars and lunar calendar integration
- 🚧 Relativistic time calculations
- 🚧 Enhanced astronomical accuracy
- 🚧 Extended space travel features

### Future Plans
- 🔮 Interstellar communication timing
- 🔮 Full solar system time zone support
- 🔮 Integration with astronomical databases
- 🔮 Advanced relativistic physics calculations

## License and Availability

- **Repository**: https://github.com/siliconprophet/CosmicCalendar/
- **NuGet Package**: https://www.nuget.org/packages/StarDate
- **Documentation**: Comprehensive inline documentation and examples

This project represents a unique fusion of practical calendar software, astronomical accuracy, and mythological storytelling, designed to serve both current needs and humanity's cosmic future.