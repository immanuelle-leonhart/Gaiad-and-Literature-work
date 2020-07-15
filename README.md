# StarDate
 The Cosmic Calendar of the Order of Life

 The StarDate struct represents a Date and Time in the Cosmic Calendar. It is designed to be able to be used interchangably with the 
 The Time struct is an alternative struct to the TimeSpan struct. 
 Supports localization into other languages, by default runs in the local system language
 StarZone object supports representation of time zones on earth but also supports timezones on Mars and in space

 StarDate constructors
 Base Constructor
 new StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int Extraticks)
 These values correspond in a straightforward manner to what they are called except for Extraticks which corresponds to every hundred nanoseconds past the millisecond, or the .NET tick system
 They correspond to months and years and days in the StarDate calendar rather than the gregorian calendar	
 defaults to local timezone according to system
 Any 
 public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks, StarZone timezone, TimeSpan error)
 Further constructors allow you to assign the timezone or the margin of error by adding additional parameters

 StarDate(BigInteger ticks, BigInteger error, StarZone timezone) works based on ticks rather than dates

 Conversion from Gregorian

 StarDate(DateTime dt), (StarDate) dt, and StarDate.FromGreg(year, month, day, hour, minute, second....) all return a converted StarDate from a Gregorian Date
 the constructor and the cast are the quickest ones as they work based on internal ticks
 StarDate.FromGreg() works by creating a DateTime and converting the ticks if possible, but otherwise will perform a much slower calculation based on the Proleptic Gregorian Calendar

 Non Static Properties

        StarDate Date
        returns the date with the time removed

        Time error
        returns margin of error for Date
        used to indicate if a date doesn't contain info for anything lower than the day or the hour for example'

        StarZone TimeZone
        returns TimeZone of Date

        DateTimeKind Kind
        returns legacy DateTimeKind Object

        Time LocalDay
        returns TimeSpan for Local Day

        BigInteger TicksPerLocalDay
        returns the Ticks Per Local Day. Depends on planet

        long fullyear
        returns the amount of years since the Big Bang

        ints quadrillion, trillion, billion, million
        return the number of quadrillion, trillion etc years since the big bang
        cap of each is 1000 as the number is taken by the higher one

        bool IsTerran
        returns true if time zone is on earth
        
        bool SupportsDaylightSavingTime
        returns true if time zone is on earth and has daylight savings time

        public Time offset
        returns utc offset for this date

        public DateTime DateTime
        returns DateTime equivalent

        ****The Following properties have set methods in addition to get methods***

        public int Year
        Returns the Year part of this StarDate. The returned value is an
        integer between 1 and 1,000,000.
        
        
        int Month
        Returns the month part of this StarDate. The returned value is an
        integer between 1 and 12.

        int WeekOfYear
        Returns the week-of-Year part of this StarDate. The returned value
        is an integer between 1 and 54.
        
        int DayOfYear
        Returns the day-of-Year part of this StarDate. The returned value
        is an integer between 1 and 378.

        int Day
        Returns the day-of-month part of this StarDate. The returned
        value is an integer between 1 and 28.

        public int Hour
        Returns the hour part of this StarDate. The returned value is an
        integer between 0 and 23.

        public int Minute
        Returns the minute part of this StarDate. The returned value is
        an integer between 0 and 59.
        
        public int Second
        Returns the second part of this StarDate. The returned value is
        an integer between 0 and 59.

        int Millisecond
        Returns the millisecond part of this StarDate. The returned value
        is an integer between 0 and 999.

        public int ExtraTicks
        Returns Ticks of this stardate that are not in a full millisecond
        integer between 1 and 10000.

        BigInteger Ticks
        Returns the tick count for this StarDate. The returned value is
        the number of 100-nanosecond intervals that have elapsed since the rounded date of the Big Bang 

        Time TimeOfDay
        Returns the time-of-day part of this StarDate. The returned value
        is a TimeSpan that indicates the time elapsed since midnight.

        string MonthName
        returns the name of the month (varies based on locale)

        string MonthSymbol
        returns the symbol of the month

        DayOfWeek DayOfWeek
        returns the Day of the Week as a DayOfTheWeek object (string casting varies based on locale)
        
        string DaySymbol
        returns the Symbol of the Day of the Week

        int Julian
        returns Julian Day of Date

        Time Atomic
        returns Atomic Clock Time

        Time Radio
        returns Time of transmissions from Earth you are currently receiving (useful for movie releases and similar)

        Time Terra
        returns time on Earth

        Time Arrival
        returns the time when your transmissions will arrive on Earth (useful for sending Merry Christmas messages to people on Earth)

 Methods

 StarDate.Parse(string input, string format)
 Parses a string based on the given format, if no format is given it will attempt to use all local formats, if it can't parse it throws an exception. (not yet implemented)
 ToString()
 Returns a string giving the date. Formatting info below for Parsing and ToString()

      Customized format patterns:
     P.S. Format in the table below is the internal number format used to display the pattern.

     Patterns   Format      Description                           Example
     =========  ==========  ===================================== ========
        "h"     "0"         hour (12-hour clock)w/o leading zero  3
        "hh"    "00"        hour (12-hour clock)with leading zero 03
        "hh*"   "00"        hour (12-hour clock)with leading zero 03

        "H"     "0"         hour (24-hour clock)w/o leading zero  8
        "HH"    "00"        hour (24-hour clock)with leading zero 08
        "HH*"   "00"        hour (24-hour clock)                  08

        "m"     "0"         minute w/o leading zero
        "mm"    "00"        minute with leading zero
        "mm*"   "00"        minute with leading zero

        "s"     "0"         second w/o leading zero
        "ss"    "00"        second with leading zero
        "ss*"   "00"        second with leading zero

        "f"     "0"         second fraction (1 digit)
        "ff"    "00"        second fraction (2 digit)
        "fff"   "000"       second fraction (3 digit)
        "ffff"  "0000"      second fraction (4 digit)
        "fffff" "00000"         second fraction (5 digit)
        "ffffff"    "000000"    second fraction (6 digit)
        "fffffff"   "0000000"   second fraction (7 digit)

        "F"     "0"         second fraction (up to 1 digit)
        "FF"    "00"        second fraction (up to 2 digit)
        "FFF"   "000"       second fraction (up to 3 digit)
        "FFFF"  "0000"      second fraction (up to 4 digit)
        "FFFFF" "00000"         second fraction (up to 5 digit)
        "FFFFFF"    "000000"    second fraction (up to 6 digit)
        "FFFFFFF"   "0000000"   second fraction (up to 7 digit)

        "t"                 first character of AM/PM designator   A
        "tt"                AM/PM designator                      AM
        "tt*"               AM/PM designator                      PM

        "d"     "0"         day w/o leading zero                  1
        "dd"    "00"        day with leading zero                 01
        "ddd"               ordinal text form                     1st
        "dddd"              ordinal text form full                First
        "dddd*"             ordinal text form full                First

        "W" WeekDay Symbol                                        ☽
        "WW" Super Short WeekDay Name                              Mo
        "WWW" Abbreviated WeekDay Name                             Mon
        "WWWW" Full WeekDay Name                                   Monday


        "M"     "0"         Month w/o leading zero                2
        "MM"    "00"        Month with leading zero               02
        "MMM"               Month Symbol                               ♎︎
        "MMMM"               short Month StarName (abbreviation)       Lib
        "MMMMM"              full Month StarName                       Libra
        "MMMMM*"             full Month StarName                       Libra

        "y"     "0"         two digit Year (Year % 100) w/o leading zero           0
        "yy"    "00"        two digit Year (Year % 100) with leading zero          00
        "yyy"   "D3"        Year                                  12000
        "yyyy"  "D4"        Year                                  12000
        "yyyyy" "D5"        Year                                  12000
        ...

        "z"     "+0;-0"     timezone offset w/o leading zero      -8
        "zz"    "+00;-00"   timezone offset with leading zero     -08
        "zzz"      "+00;-00" for hour offset, "00" for minute offset  full timezone offset   -07:30
        "zzz*"  "+00;-00" for hour offset, "00" for minute offset   full timezone offset   -08:00

        "K"    -Local       "zzz", e.g. -08:00
               -Utc         "'Z'", representing UTC
               -Unspecified ""
               -StarDateOffset      "zzzzz" e.g -07:30:15

        "g"                the current era StarName                  A.M.
	"gg*"		   name of the surrent era full		     Anno Manu

        ":"                 time separator                        : -- DEPRECATED - Insert separator directly into pattern (eg: "H.mm.ss")
        "/"                 date separator                        /-- DEPRECATED - Insert separator directly into pattern (eg: "M-dd-yyyy")
        "'"                 quoted string                         'ABC' will insert ABC into the formatted string.
        '"'                 quoted string                         "ABC" will insert ABC into the formatted string.
        "%"                 used to quote a single pattern characters      E.g.The format character "%y" is to print two digit Year.
        "\"                 escaped character                     E.g. '\d' insert the character 'd' into the format string.
        other characters    insert the character into the format string.

    Pre-defined format characters:
        (U) to indicate Universal time is used.
        (G) to indicate Gregorian calendar is used.

        Format              Description                             Real format                             Example
        =========           =================================       ======================                  =======================
        "d"                 short date                              culture-specific                        10/28/11999
        "D"                 long data                               culture-specific                        Sunday, Virgo 28, 11999
        "f"                 full date (long date + short time)      culture-specific                        Sunday, Virgo 28, 11999 2:00 AM
        "F"                 full date (long date + long time)       culture-specific                        Sunday, Virgo 28, 11999 2:00:00 AM
        "g"                 general date (short date + short time)  culture-specific                        10/28/11999 2:00 AM
        "G"                 general date (short date + long time)   culture-specific                        10/28/11999 2:00:00 AM
        "m"/"M"             Month/Day date                          culture-specific                        Virgo 31
(G)     "o"/"O"             Round Trip XML                          "yyyy-MM-ddTHH:mm:ss.fffffffK"          11999-10-28 02:00:00.0000000Z
(G)     "r"/"R"             RFC 1123 date,                          "WWW, dd MMM yyyy HH':'mm':'ss 'GMT'"   Sun, 28 Vir 11999 10:00:00 GMT
(G)     "s"                 Sortable format, based on ISO 8601.     "yyyy-MM-dd'T'HH:mm:ss"                 11999-10-28T02:00:00
                                                                    ('T' for local time)
        "t"                 short time                              culture-specific                        2:00 AM
        "T"                 long time                               culture-specific                        2:00:00 AM
(G)     "u"                 Universal time with sortable format,    "yyyy'-'MM'-'dd HH':'mm':'ss'Z'"        11999-10-28 10:00:00Z
                            based on ISO 8601.
(U)     "U"                 Universal time with full                culture-specific                        Sunday, Virgo 31, 11999 10:00:00 AM
                            (long date + long time) format
                            "y"/"Y"             Year/Month day                          culture-specific                        Virgo, 11999




















 MakeChart(string path, int gregyear)
 writes a chart in csv form of date conversions for the given year at the destination given in the path
 CompareTo(StarDate other)
 Implements standard CompareTo Method


 Operators

 	StarDate = Stardate + TimeSpan
 	StarDate = Stardate - TimeSpan
 	==
 	!=
 	<
 	>
 	<=
 	>=
 	StarDate++ adds a day
 	StarDate-- subtracts a day
 	DateTimes and StarDates implicitly cast into each other
 	Implicit Casting into string implements ToString()