using System;
using System.Collections.Generic;
using System.Diagnostics.Contracts;
using System.Globalization;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text;
using System.Xml;
using System.Xml.Schema;
using System.Xml.Serialization;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;

namespace StarLib
{



    // This value type represents a date and time.  Every StarDate
    // object has a private field (Ticks) of type Int64 that stores the
    // date and time as the number of 100 nanosecond intervals since
    // the Big Bang (fixed to 14 billion years before the beginning of the Holocene Calendar)
    //
    // Starting from V2.0, StarDate also stored some context about its time
    // zone in the form of a 3-state value representing Unspecified, Utc or
    // Local. This is stored in the two top bits of the 64-bit numeric value
    // with the remainder of the bits storing the tick count. This information
    // is only used during time zone conversions and is not part of the
    // identity of the StarDate. Thus, operations like Compare and Equals
    // ignore this state. This is to stay compatible with earlier behavior
    // and performance characteristics and to avoid forcing  people into dealing
    // with the effects of daylight savings. Note, that this has little effect
    // on how the StarDate works except in a context where its specific time
    // zone is needed, such as during conversions and some parsing and formatting
    // cases.
    //
    // There is also 4th state stored that is a special type of Local value that
    // is used to avoid data loss when round-tripping between local and UTC time.
    // See below for more information on this 4th state, although it is
    // effectively hidden from most users, who just see the 3-state DateTimeKind
    // enumeration.
    //
    // For compatability, StarDate does not serialize the Kind data when used in
    // binary serialization.
    //
    // For a description of various calendar issues, look at
    //
    // Calendar Studies web site, at
    // http://serendipity.nofadz.com/hermetic/cal_stud.htm.
    //
    //
    /*
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

        "g*"                the current era StarName                  A.D.

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
(G)     "i"/"I"             Sortable format, based on ISO 8601.     "yyyy-MM-dd'T'HH:mm:ss"                 11999-10-28T02:00:00
        "s"/"S"             Short DateTime Format                   "yyyy-MM-dd HH:mm:ss kk"                11999-10-28 02:00:00 PST
        "l"/"L"             Long DateTime Format                    "WWWW, MMMMM ddd yyyyy h:mm tt kk"      Sunday, Virgo 28th, 11999 2:00 AM PST
                                                                    ('T' for local time)
        "t"                 short time                              culture-specific                        2:00 AM
        "T"                 long time                               culture-specific                        2:00:00 AM
(G)     "u"                 Universal time with sortable format,    "yyyy'-'MM'-'dd HH':'mm':'ss'Z'"        11999-10-28 10:00:00Z
                            based on ISO 8601.
(U)     "U"                 Universal time with full                culture-specific                        Sunday, Virgo 31, 11999 10:00:00 AM
                            (long date + long time) format
                            "y"/"Y"             Year/Month day                          culture-specific                        Virgo, 11999

    */
    [StructLayout(LayoutKind.Auto)]
    //[Serializable] readd serializable
    public struct StarDate : IComparable<StarDate>, IEquatable<StarDate>, IComparable, IFormattable, IConvertible, IComparable<DateTime>, IEquatable<DateTime>, IXmlSerializable
    {

        // Number of 100ns _ticks per time unit
        internal static Time MillisecondTime = new Time(10000);
        internal const int TicksPerMillisecond = 10000;
        internal static Time SecondTime = MillisecondTime * 1000;
        internal const int TicksPerSecond = TicksPerMillisecond * 1000;
        internal static Time MinuteTime = SecondTime * 60;
        internal const long TicksPerMinute = TicksPerSecond * 60;
        internal static Time HourTime = MinuteTime * 60;
        internal const long TicksPerHour = TicksPerMinute * 60;
        public static Time DayTime = HourTime * 24;
        internal const long TicksPerDay = TicksPerHour * 24;
        internal static Time Decidi = DayTime / 10;
        internal static Time Centidi = DayTime / 100;
        internal static Time Millidi = DayTime / 1000;
        internal static Time Microdi = DayTime / 1000000;
        internal static Time Nanodi = DayTime / 1000000000; //Only Metric Time needed
        internal static Time Sol = 1.02749125 * DayTime;
        internal static Time week = DayTime * 7;
        internal const long TicksPerWeek = TicksPerDay * 7;
        internal const int DaysPerWeek = 7;
        internal static Time MonthTime = week * 4;
        internal const long TicksPerMonth = TicksPerDay * 28;
        internal const int DaysPerMonth = DaysPerWeek * 4;
        public static Time YearTime = week * 52;
        internal static BigInteger TicksPerYear = TicksPerWeek * 52;
        internal const int DaysPerYear = DaysPerMonth * 13;
        internal static Time Leap = YearTime + week;
        internal static BigInteger TicksPerLeapYear = TicksPerYear + TicksPerWeek;
        internal const int DaysPerLeapYear = DaysPerYear + DaysPerWeek;
        internal static Time DoubleLeap = Leap + week;
        internal static BigInteger TicksPerDoubleLeap = TicksPerLeapYear + TicksPerWeek;
        internal const int DaysPerDoubleLeap = DaysPerLeapYear + DaysPerWeek;
        internal static Time Sixyear = YearTime * 6 + week; //6 years, 313 weeks;
        internal static BigInteger TicksPerSixYears = TicksPerYear * 6 + TicksPerWeek;
        internal const int DaysPerSixYears = DaysPerYear * 6 + DaysPerWeek;
        internal static Time Seventy_Eight = Sixyear * 13 + week; //78 years, 4070 weeks;
        internal static BigInteger TicksPerSeventyEightYears = TicksPerSixYears * 13 + TicksPerWeek;
        internal const int DaysPer78Years = DaysPerSixYears * 13 + DaysPerWeek;
        internal static Time AverageYear = DayTime * 365.256410256;
        internal const int DaysPerAverageYear = DaysPer78Years / 78;
        internal static BigInteger TicksPerAverageYear = TicksPerSeventyEightYears / 78;
        public const double DaysPerSiderealYear = 365.25636;
        internal const int k = 1000;
        internal static BigInteger TicksPerThousand = TicksPerAverageYear * 1000;
        internal const long DaysPer100k = 1282 * DaysPer78Years + 4 * DaysPerYear;
        public static BigInteger TicksPer100k = (BigInteger)DaysPer100k * (BigInteger)TicksPerDay;
        internal const long DaysPerMillion = DaysPer100k * 10;
        public static BigInteger TicksPerMillion = DaysPerMillion * (BigInteger)TicksPerDay;
        private static readonly Time m = new Time(TicksPerMillion);
        internal const long DaysPerBillion = DaysPerMillion * 1000;
        public static BigInteger TicksPerBillion = TicksPerMillion * 1000;
        private static readonly Time b = new Time(TicksPerBillion);
        internal const long DaysPerTrillion = DaysPerBillion * 1000;
        internal const long DaysPerQuadrillion = DaysPerTrillion * 1000;
        private static readonly StarDate manu = new StarDate(14 * TicksPerBillion, UTC);
        private static readonly StarDate maxManu = new StarDate(14 * TicksPerBillion + TicksPerMillion, UTC);
        internal static readonly StarDate maya = manu + 154 * Seventy_Eight; //10k BC + 154 * 78 = 12012
        internal static readonly DateTime maya_net = new DateTime(2011, 12, 26); //2011-12-26
        internal static readonly StarDate ADStart = maya - new Time(maya_net.Ticks);
        internal static readonly StarDate julian = maya - 2455921 * DayTime;
        internal static readonly Time tr = b * 1000;

        // Number of milliseconds per time unit
        private const int MillisPerSecond = 1000;
        private const int MillisPerMinute = MillisPerSecond * 60;
        private const int MillisPerHour = MillisPerMinute * 60;
        private const int MillisPerDay = MillisPerHour * 24;
        private const int MillisPerWeek = MillisPerDay * 7;
        private const long MillisPerMonth = (long)MillisPerWeek * 4;
        private const long MillisPerYear = MillisPerMonth * 13;

        // Number of days in a non-leap Year
        private const int DaysPerYear2 = 365;
        // Number of days in 4 years
        private const int DaysPer4Years = DaysPerYear2 * 4 + 1;       // 1461
        // Number of days in 100 years
        private const int DaysPer100Years = DaysPer4Years * 25 - 1;  // 36524
        // Number of days in 400 years
        private const int DaysPer400Years = DaysPer100Years * 4 + 1; // 146097

        // Number of days from 1/1/0001 to 12/31/1600
        private const int DaysTo1601 = DaysPer400Years * 4;          // 584388
        // Number of days from 1/1/0001 to 12/30/1899
        private const int DaysTo1899 = DaysPer400Years * 4 + DaysPer100Years * 3 - 367;
        // Number of days from 1/1/0001 to 12/31/1969
        internal const int DaysTo1970 = DaysPer400Years * 4 + DaysPer100Years * 3 + DaysPer4Years * 17 + DaysPerYear; // 719,162
        // Number of days from 1/1/0001 to 12/31/9999
        private const int DaysTo10000 = DaysPer400Years * 25 - 366;  // 3652059

        internal const long MinTicks = 0;
        internal const long MaxTicks = DaysTo10000 * TicksPerDay - 1;
        private const long MaxMillis = (long)DaysTo10000 * MillisPerDay;

        private const long FileTimeOffset = DaysTo1601 * TicksPerDay;
        private const long DoubleDateOffset = DaysTo1899 * TicksPerDay;
        // The minimum OA date is 0100/01/01 (Note it's Year 100).
        // The maximum OA date is 9999/12/31
        private const long OADateMinAsTicks = (DaysPer100Years - DaysPerYear) * TicksPerDay;
        // All OA dates must be greater than (not >=) OADateMinAsDouble
        private const double OADateMinAsDouble = -657435.0;
        // All OA dates must be less than (not <=) OADateMaxAsDouble
        private const double OADateMaxAsDouble = 2958466.0;

        private const int DatePartQuadrillion = -5;
        private const int DatePartTrillion = -4;
        private const int DatePartBillion = -3;
        private const int DatePartMillion = -2;
        private const int DatePart100k = -1;
        private const int DatePartYear = 0;
        private const int DatePartDayOfYear = 1;
        private const int DatePartMonth = 2;
        private const int DatePartDay = 3;
        private const int DatePartDayOfWeek = 4;
        private const int PlaceHolder = 9999999;

        //internal static readonly bool s_isLeapSecondsSupportedSystem = SystemSupportLeapSeconds();

        private static readonly int[] DaysToMonth365 = {
            0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
        private static readonly int[] DaysToMonth366 = {
            0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};
        private const UInt64 ticksMask = 0x3FFFFFFFFFFFFFFF;
        private const UInt64 FlagsMask = 0xC000000000000000;
        private const UInt64 LocalMask = 0x8000000000000000;
        private const UInt64 ticksCeiling = 0x4000000000000000;
        private const UInt64 KindUnspecified = 0x0000000000000000;
        private const UInt64 KindUtc = 0x4000000000000000;
        private const UInt64 KindLocal = 0x8000000000000000;
        private const UInt64 KindLocalAmbiguousDst = 0xC000000000000000;
        private const Int32 KindShift = 62;

        private const String TicksField = "_ticks";
        private const String DateDataField = "internalTicks";

        // The data is stored as an unsigned 64-bit integer
        //   Bits 01-62: The value of 100-nanosecond _ticks where 0 represents 1/1/0001 12:00am, up until the value
        //               12/31/9999 23:59:59.PlaceHolder
        //   Bits 63-64: A four-state value that describes the DateTimeKind value of the date time, with a 2nd
        //               value for the rare case where the date time is local, but is in an overlapped daylight
        //               savings time hour and it is in daylight savings time. This allows distinction of these
        //               otherwise ambiguous local times and prevents data loss when round tripping from Local to
        //               UTC time.
        private BigInteger internalTicks;
        private Accuracy accuracy;
        private StarZone _timeZone;
        private static IEnumerable<string> allFormats;
        private static IEnumerable<StarDate> testYear;

        private static StarDate maya1;
        public static bool LongDefault = false; //switches whether the default tostring method prints a long date or a short date
        //private static string currentCulture;
        private static List<string> formats;
        private static bool acceptoverflow = false; //determines whether setters throw errors related to leap year overflows or set the date to the next year
        private static StarDate[] eras;
        private static int manuInt = -1;
        //private static StarCulture currentCulture;

        //private string defaultFormat;

        //private int era;

        //private bool ageOfManu;

        //private Accuracy /*marginOfError*/;

        //private bool hasMonth;

        //private BigInteger error1;

        //private int[] vs;




        //private StarZone timezone;

        public StarDate TickTimeZoneConvert(StarZone z) //converts a timezone by treating the utc ticks in a StarDate as though they were the ticks of that timezone
        {
            return new StarDate(Year, Month, Day, Hour, Minute, Second, Millisecond);
        }



        //public static StarDate StarHanukkah() //gives the date of hannukkah for this year
        //{
        //    return new StarDate(GregHanukkah());
        //}

        //public static void MakeChart()
        //{
        //    MakeChart("");
        //}

        //public static void MakeChart(int gregyear)
        //{
        //    MakeChart("", gregyear);
        //}

        //public static void MakeChart(string v) //makes a chart for a year at the designated path
        //{
        //    StarDate.MakeChart(v, DateTime.Now.Year);
        //}

        //public static void MakeChart(string path, int gregyear) //makes a chart for a year at the designated path
        //{
        //    StreamWriter chart = new StreamWriter(path + "CosmicCalendar.csv");
        //    StarDate mi = StarDate.FromGreg(gregyear, 6, 2);
        //    int y = mi.Year;
        //    StarDate[] starDates = new StarDate[] { StarDate.FromGreg(gregyear, 1, 1), StarDate.FromGreg(gregyear, 12, 31), new StarDate(y, 1, 1), new StarDate(y + 1, 1, 1).AddDays(-1) };
        //    Array.Sort(starDates);
        //    StarDate dt = starDates[0];
        //    StarDate end = starDates[3];
        //    chart.WriteLine("short stardate, long stardate, Star Year, Star Month, Star Month Name, Month Symbol, Day of Star Year, Day of Star Month, Weekday, Weekday Symbol, short gregdate, long gregdate, gregyear, gegmonth, gregmonth name, greg day of year, greg day of month");
        //    while (dt <= end)
        //    {
        //        string data = "";
        //        data += dt.ToShortDateString(); data += ",";
        //        data += dt.ToLongDateString(); data += ",";
        //        data += dt.Year; data += ",";
        //        data += dt.Month; data += ",";
        //        data += dt.MonthName; data += ",";
        //        data += dt.MonthSymbol; data += ",";
        //        data += dt.DayOfYear; data += ",";
        //        data += dt.Day; data += ",";
        //        data += dt.DayOfWeek; data += ",";
        //        data += dt.DaySymbol; data += ",";
        //        data += dt.DateTime.ToShortDateString(); data += ",";
        //        data += dt.DateTime.ToLongDateString(); data += ",";
        //        data += dt.DateTime.Year; data += ",";
        //        data += dt.DateTime.Month; data += ",";
        //        data += dt.DateTime.ToString("MMMMMMMMM");
        //        data += dt.DateTime.DayOfYear; data += ",";
        //        data += dt.DateTime.Day; data += ",";
        //        chart.WriteLine(data);
        //        dt++;
        //    }
        //    chart.Flush();
        //    chart.Close();
        //    //////throw new NotImplementedException();
        //}

        internal static StarDate AbstractDate(Time timeSpanInfo)
        {
            StarDate dt = new StarDate(timeSpanInfo);

            dt.TimeZone = StarZone.Local;
            //dt.arraylength = 10;
            dt.accuracy = 0;
            return dt;
        }



        //public static StarDate StarHanukkah(DateTime dt) //
        //{
        //    return new StarDate(GregHanukkah(dt));
        //}

        //public static StarDate StarHanukkah(StarDate dt)//
        //{
        //    return new StarDate(GregHanukkah(dt));
        //}

        //public static DateTime GregHanukkah()//
        //{
        //    return GregHanukkah(DateTime.Now);
        //}

        //public static DateTime GregHanukkah(DateTime now)//
        //{
        //    System.Globalization.Calendar HebCal = new HebrewCalendar();
        //    int i = now.Year;
        //    DateTime h = new DateTime(i, 11, 1);
        //    int hebyear = HebCal.GetYear(now);
        //    DateTime Hanukkah = new DateTime(hebyear, 3, 25, new HebrewCalendar());
        //    return Hanukkah;
        //}


        //public static DateTime GregHanukkah(StarDate dt)//
        //{
        //    DateTime o = new StarDate(dt.Year, 12, 1).DateTime;
        //    return GregHanukkah(o);
        //}





        internal static StarDate MathFromGreg(int[] v)
        {
            return MathFromGreg(v[0], v[1], v[2]);
        }












        public StarDate EasterDate()
        {
            return StarEaster((int)this.gregyear());
        }

        public static StarDate StarEaster(int year)
        {
            DateTime easter = StarDate.GregEaster(year);
            return new StarDate(easter);
        }

        public static StarDate StarThanksgiving(int year)
        {
            DateTime Thanksgiving = StarDate.GregThanksgiving(year);
            return new StarDate(Thanksgiving);
        }



        public bool Easter()
        {
            return this.Date == this.EasterDate();
        }




        internal static StarDate MathFromGreg(int v1, int v2, int v3)
        {
            return MathFromGreg(v1, v2, v3, 0, 0, 0, 0);
        }


        public long gregyear()
        {
            if (this.Year > 10000)
            {
                return this.Year - 10000;
            }
            else
            {
                return this.Year - 10001;
            }
        }

        public static DateTime GregThanksgiving(int year)
        {
            DateTime dt = new DateTime(year, 11, 1);
            while (dt.DayOfWeek.ToString() != "Thursday")
            {
                dt = dt.AddDays(1);
            }
            return dt.AddDays(21);
        }

        public static DateTime GregEaster(int year)
        {
            int a = year % 19;
            int b = year / 100;
            int c = (b - (b / 4) - ((8 * b + 13) / 25) + (19 * a) + 15) % 30;
            int d = c - (c / 28) * (1 - (c / 28) * (29 / (c + 1)) * ((21 - a) / 11));
            int e = d - ((year + (year / 4) + d + 2 - b + (b / 4)) % 7);
            int month = 3 + ((e + 40) / 44);
            int day = e + 28 - (31 * (month / 4));
            return new DateTime(year, month, day);
        }



        int IComparable<StarDate>.CompareTo(StarDate other)
        {
            return this.CompareTo(other);
        }

        bool IEquatable<StarDate>.Equals(StarDate other)
        {
            return this.Equals(other);
        }



        public static StarDate GregParse(string input)
        {
            DateTime dt;
            try
            {
                dt = DateTime.Parse(input);
                return new StarDate(dt);
            }
            catch (System.FormatException)
            {
                string[] parsedinput = input.Split(' ');
                string modifier = parsedinput[0];
                if (modifier == "Star")
                {
                    return StarDate.Parse(input.Substring(4));
                }
                else if ((parsedinput[parsedinput.Length - 1] == "BC") || (parsedinput[parsedinput.Length - 1] == "B.C."))
                {
                    //BC Year
                    //DATE ABT 47000 B.C.
                    //modifier = parsedinput[0];
                    long year2;
                    try
                    {
                        year2 = long.Parse(parsedinput[1]);
                    }
                    catch (FormatException)
                    {
                        year2 = BCParse(parsedinput);
                    }
                    StarDate sd = ADStart - year2 * StarDate.YearTime;
                    sd.TimeZone = StarZone.Local;
                    return sd;
                    //////throw new NotImplementedException();
                }
                //else if (modifier == "BET")
                //{
                //    try
                //    {
                //        StarDate dt1 = StarDate.GregParse(parsedinput[1] + " " + parsedinput[2] + " " + parsedinput[3]);
                //        StarDate dt2 = StarDate.GregParse(parsedinput[5] + " " + parsedinput[6] + " " + parsedinput[7]);
                //        return Between(dt1, dt2);
                //    }
                //    catch (IndexOutOfRangeException)
                //    {
                //        return Between(StarDate.FromGreg(int.Parse(parsedinput[1])), StarDate.FromGreg(int.Parse(parsedinput[3])));
                //    }
                //}
                else if (modifier == "ABT")
                {
                    int l = int.Parse(parsedinput[1]);
                    return StarDate.FromGreg(l);
                }
                else
                {
                    string new_input = "";
                    int i = 1;
                    while (i < parsedinput.Length)
                    {
                        new_input = new_input + " " + parsedinput[i];
                        i++;
                    }
                    try
                    {
                        return (StarDate)DateTime.Parse(new_input);
                    }
                    catch (FormatException)
                    {
                        try
                        {
                            return (StarDate)DateTime.Parse(parsedinput[1] + " " + parsedinput[2] + " " + parsedinput[3]);
                        }
                        catch (IndexOutOfRangeException)
                        {
                            try
                            {
                                int year = int.Parse(input);
                                return StarDate.FromGreg(year);
                            }
                            catch (FormatException)
                            {
                                try
                                {
                                    string[] decomma = input.Split(',');
                                    string v = "";
                                    int j = 0;
                                    while (j < decomma.Length)
                                    {
                                        v = v + decomma[j++];
                                    }
                                    ////////////Console.WriteLine(path);
                                    int year = int.Parse(v);
                                    return StarDate.FromGreg(year);
                                }
                                catch (FormatException)
                                {
                                    throw new NotImplementedException();
                                    //if ((parsedinput[1] == "AND"))
                                    //{
                                    //    StarDate a = StarDate.FromGreg(int.Parse(parsedinput[0]));
                                    //    StarDate b = StarDate.FromGreg(int.Parse(parsedinput[2]));
                                    //    return Between(a, b);
                                    //}
                                }
                            }

                        }
                    }
                }
            }
        }



        private static long BCParse(string[] parsedinput)
        {
            int i = 0;
            while (i < parsedinput.Length)
            {
                ////////////Console.WriteLine(i + " " + parsedinput[i++]);
            }
            return long.Parse(parsedinput[0]);
            //////throw new NotImplementedException();
        }




        private void adderror(Accuracy error)
        {
            this.accuracy = error;
        }

        // Returns a StarDate representing the current date. The date part
        // of the returned value is the current date, and the time-of-day part of
        // the returned value is zero (midnight).
        //


        public override string ToString()
        {
            return this.ToString(StarCulture.CurrentCulture);
        }

        private string ToString(StarCulture local)
        {
            if (StarDate.LongDefault)
            {
                return ToString(local, "L");
            }
            else
            {
                return ToString(local, "S");
            }
        }

        public string ToString(string format, string lang)
        {
            return this.ToString(StarCulture.GetLocale(lang), format);
        }

        public string ToString(string format)
        {
            return this.ToString(StarCulture.CurrentCulture, format);
        }

        private string ToString(StarCulture local, string format)
        {
            return local.StarDateString(this, format);
        }

        private string addzero(long v)
        {
            if (v < 10)
            {
                return "0" + v;
            }
            else
            {
                return "" + v;
            }
        }

        // Returns a given date part of this StarDate. This method is used
        // to compute the Year, day-of-Year, month, or day part.
        private long GetDatePart(int part)
        {
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            if (IsTerran == false)
            {
                throw new NotImplementedException();
            }
            int y100k = (int)(n / DaysPer100k);
            if (part == DatePart100k) return 100 * k * y100k;
            n -= y100k * DaysPer100k;
            int y78 = (int)(n / DaysPer78Years);
            n -= y78 * DaysPer78Years;
            int y6 = (int)(n / DaysPerSixYears);
            if (y6 == 13) y6 = 12;
            n -= y6 * DaysPerSixYears;
            int y1 = (int)(n / DaysPerYear);
            if (y1 == 6) y1 = 5;
            if (part == DatePartYear) return 100 * k * (long)y100k + 78 * (long)y78 + 6 * (long)y6 + (long)y1;
            n -= y1 * DaysPerYear;
            int d = (int)n + 1;
            if (part == DatePartDayOfYear) return d;
            if (part == DatePartMonth) return ((d - 1) / 28) + 1;
            d %= 28;
            if (d == 0) d = 28;
            if (part == DatePartDay) return d;
            else if (part == DatePartDayOfWeek) return d % 7;
            else
            {
                return 19;
            }
        }

        // Exactly the same as GetDatePart(int part), except computing all of
        // Year/month/day rather than just one of them.  Used when all three
        // are needed rather than redoing the computations for each.

        public void GetDatePart(out long year)
        {
            year = FullYear;
        }

        public void GetDatePart(out long year, out long month)
        {
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            if (IsTerran)
            {
                int y100k = (int)(n / DaysPer100k);
                n -= y100k * DaysPer100k;
                int y78 = (int)(n / DaysPer78Years);
                n -= y78 * DaysPer78Years;
                int y6 = (int)(n / DaysPerSixYears);
                if (y6 == 13) y6 = 12;
                n -= y6 * DaysPerSixYears;
                int y1 = (int)(n / DaysPerYear);
                if (y1 == 6) y1 = 5;
                year = 100 * k * (long)y100k + 78 * (long)y78 + 6 * (long)y6 + (long)y1;
                n -= y1 * DaysPerYear;
                int d = (int)n + 1;
                month = ((d - 1) / 28) + 1;
                //d %= 28;
                //if (d == 0) d = 28;
                //day = d;
            }
            else
            {
                throw new NotImplementedException();
            }

        }

        public void GetDatePart(out long year, out long month, out long day)
        {
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            if (IsTerran)
            {
                int y100k = (int)(n / DaysPer100k);
                n -= y100k * DaysPer100k;
                int y78 = (int)(n / DaysPer78Years);
                n -= y78 * DaysPer78Years;
                int y6 = (int)(n / DaysPerSixYears);
                if (y6 == 13) y6 = 12;
                n -= y6 * DaysPerSixYears;
                int y1 = (int)(n / DaysPerYear);
                if (y1 == 6) y1 = 5;
                year = 100 * k * (long)y100k + 78 * (long)y78 + 6 * (long)y6 + (long)y1;
                n -= y1 * DaysPerYear;
                int d = (int)n + 1;
                month = ((d - 1) / 28) + 1;
                d %= 28;
                if (d == 0) d = 28;
                day = d;
            }
            else
            {
                throw new NotImplementedException();
            }

        }

        public void GetDatePart(out long year, out long month, out long day, out long hour)
        {
            GetDatePart(out year, out month, out day);
            hour = Hour;
        }

        public void GetDatePart(out long year, out long month, out long day, out long hour, out long min)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min);
        }

        public void GetDatePart(out long year, out long month, out long day, out long hour, out long min, out long sec)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min, out sec);
        }

        public void GetDatePart(out long year, out long month, out long day, out long hour, out long min, out long sec, out long millisec)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min, out sec, out millisec);
        }

        public void GetDatePart(out long year, out long month, out long day, out long hour, out long min, out long sec, out long millisec, out long ticks)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min, out sec, out millisec, out ticks);
        }

        /// <summary>
        /// //////////////////////////////////////////////////////////////////////
        /// </summary>
        /// <param name="vs"></param>
        /// 

        public void GetDatePart(out int year)
        {
            year = Year;
        }

        public void GetDatePart(out int year, out int month)
        {
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            if (IsTerran)
            {
                int y100k = (int)(n / DaysPer100k);
                n -= y100k * DaysPer100k;
                int y78 = (int)(n / DaysPer78Years);
                n -= y78 * DaysPer78Years;
                int y6 = (int)(n / DaysPerSixYears);
                if (y6 == 13) y6 = 12;
                n -= y6 * DaysPerSixYears;
                int y1 = (int)(n / DaysPerYear);
                if (y1 == 6) y1 = 5;
                long y = 100 * k * (long)y100k + 78 * (long)y78 + 6 * (long)y6 + (long)y1;
                year = ToManu(y);
                n -= y1 * DaysPerYear;
                int d = (int)n + 1;
                month = ((d - 1) / 28) + 1;
                //d %= 28;
                //if (d == 0) d = 28;
                //day = d;
            }
            else
            {
                throw new NotImplementedException();
            }

        }

        public void GetDatePart(out int year, out int month, out int day)
        {
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            if (IsTerran)
            {
                int y100k = (int)(n / DaysPer100k);
                n -= y100k * DaysPer100k;
                int y78 = (int)(n / DaysPer78Years);
                n -= y78 * DaysPer78Years;
                int y6 = (int)(n / DaysPerSixYears);
                if (y6 == 13) y6 = 12;
                n -= y6 * DaysPerSixYears;
                int y1 = (int)(n / DaysPerYear);
                if (y1 == 6) y1 = 5;
                long y = 100 * k * (long)y100k + 78 * (long)y78 + 6 * (long)y6 + (long)y1;
                year = ToManu(y);
                n -= y1 * DaysPerYear;
                int d = (int)n + 1;
                month = ((d - 1) / 28) + 1;
                d %= 28;
                if (d == 0) d = 28;
                day = d;
            }
            else
            {
                throw new NotImplementedException();
            }

        }

        public void GetDatePart(out int year, out int month, out int day, out int hour)
        {
            GetDatePart(out year, out month, out day);
            hour = Hour;
        }

        public void GetDatePart(out int year, out int month, out int day, out int hour, out int min)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min);
        }

        private void GetTimePart(out int hour, out int min)
        {
            long h, m;
            GetTimePart(out h, out m);
            hour = (int)h;
            min = (int)m;
        }

        public void GetDatePart(out int year, out int month, out int day, out int hour, out int min, out int sec)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min, out sec);
        }

        private void GetTimePart(out int hour, out int min, out int sec)
        {
            long h, m, s;
            GetTimePart(out h, out m, out s);
            hour = (int)h;
            min = (int)m;
            sec = (int)s;
        }

        public void GetDatePart(out int year, out int month, out int day, out int hour, out int min, out int sec, out int millisec)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min, out sec, out millisec);
        }

        private void GetTimePart(out int hour, out int min, out int sec, out int millisec)
        {
            long h, m, s, mil;
            GetTimePart(out h, out m, out s, out mil);
            hour = (int)h;
            min = (int)m;
            sec = (int)s;
            millisec = (int)mil;
        }

        public void GetDatePart(out int year, out int month, out int day, out int hour, out int min, out int sec, out int millisec, out int ticks)
        {
            GetDatePart(out year, out month, out day);
            GetTimePart(out hour, out min, out sec, out millisec, out ticks);
        }

        private void GetTimePart(out int hour, out int min, out int sec, out int millisec, out int ticks)
        {
            long h, m, s, mil, t;
            GetTimePart(out h, out m, out s, out mil, out t);
            hour = (int)h;
            min = (int)m;
            sec = (int)s;
            millisec = (int)mil;
            ticks = (int)t;
        }

        public void GetDatePart(out int[] vs)
        {
            int y, mo, d, h, mi, s, ms, t;
            GetDatePart(out y, out mo, out d, out h, out mi, out s, out ms, out t);
            vs = new int[] { y, mo, d, h, mi, s, ms, t };
        }

        public void GetDatePart(out long[] vs)
        {
            long y, mo, d, h, mi, s, ms, t;
            GetDatePart(out y, out mo, out d, out h, out mi, out s, out ms, out t);
            vs = new long[] { y, mo, d, h, mi, s, ms, t };
        }

        public long[] GetDateParts()
        {
            return GetDateParts(8);
        }

        public long[] GetDateParts(int length)
        {
            if (length < 1) length = 8;
            long[] vs = new long[length];
            switch (vs.Length)
            {
                case 1:
                    GetDatePart(out vs[0]);
                    break;
                case 2:
                    GetDatePart(out vs[0], out vs[1]);
                    break;
                case 3:
                    GetDatePart(out vs[0], out vs[1], out vs[2]);
                    break;
                case 4:
                    GetDatePart(out vs[0], out vs[1], out vs[2], out vs[3]);
                    break;
                case 5:
                    GetDatePart(out vs[0], out vs[1], out vs[2], out vs[3], out vs[4]);
                    break;
                case 6:
                    GetDatePart(out vs[0], out vs[1], out vs[2], out vs[3], out vs[4], out vs[5]);
                    break;
                case 7:
                    GetDatePart(out vs[0], out vs[1], out vs[2], out vs[3], out vs[4], out vs[5], out vs[6]);
                    break;
                case 8:
                    GetDatePart(out vs[0], out vs[1], out vs[2], out vs[3], out vs[4], out vs[5], out vs[6], out vs[7]);
                    break;
                default:
                    GetDatePart(out vs); break;
            }
            return vs;
        }

        private void GetDatePart(out Dictionary<string, long> keyValuePairs)
        {
            long[] values;
            GetDatePart(out values);
            string[] keys = new string[] { "Year", "Month", "Day", "Hour", "Minute", "Second", "Millisecond", "Ticks" };
            int i = 0;
            keyValuePairs = new Dictionary<string, long>();
            while (i < values.Length)
            {
                keyValuePairs.Add(keys[i], values[i]);
                i++;
            }
        }

        public long[] GetDatePart()
        {
            long[] values;
            GetDatePart(out values);
            return values;
        }

        public void GetTimePart(out long hour, out long min)
        {
            Int64 t = (long)TimeOfDay.Ticks;
            hour = (int)(t / TicksPerHour);
            t %= TicksPerHour;
            min = (int)(t / TicksPerMinute);
            //t %= TicksPerMinute;
            //sec = (int)(t / TicksPerSecond);
            //t %= TicksPerSecond;
            //millisec = (int)(t / TicksPerMillisecond);
            //t %= TicksPerMillisecond;
            //ticks = (int)t;

        }

        public void GetTimePart(out long hour, out long min, out long sec)
        {
            Int64 t = (long)TimeOfDay.Ticks;
            hour = (int)(t / TicksPerHour);
            t %= TicksPerHour;
            min = (int)(t / TicksPerMinute);
            t %= TicksPerMinute;
            sec = (int)(t / TicksPerSecond);
            //t %= TicksPerSecond;
            //millisec = (int)(t / TicksPerMillisecond);
            //t %= TicksPerMillisecond;
            //ticks = (int)t;

        }

        public void GetTimePart(out long hour, out long min, out long sec, out long millisec)
        {
            Int64 t = (long)TimeOfDay.Ticks;
            hour = (int)(t / TicksPerHour);
            t %= TicksPerHour;
            min = (int)(t / TicksPerMinute);
            t %= TicksPerMinute;
            sec = (int)(t / TicksPerSecond);
            t %= TicksPerSecond;
            millisec = (int)(t / TicksPerMillisecond);
            //t %= TicksPerMillisecond;
            //ticks = (int)t;

        }

        public void GetTimePart(out long hour, out long min, out long sec, out long millisec, out long ticks)
        {
            Int64 t = (long)TimeOfDay.Ticks;
            hour = (int)(t / TicksPerHour);
            t %= TicksPerHour;
            min = (int)(t / TicksPerMinute);
            t %= TicksPerMinute;
            sec = (int)(t / TicksPerSecond);
            t %= TicksPerSecond;
            millisec = (int)(t / TicksPerMillisecond);
            t %= TicksPerMillisecond;
            ticks = (int)t;

        }

        private int GregDatePart(int part)
        {
            try
            {
                switch (part)
                {
                    case DatePartYear:
                        return DateTime.Year;
                    case DatePartDayOfYear:
                        return DateTime.DayOfYear;
                    case DatePartMonth:
                        return DateTime.Month;
                    case DatePartDay:
                        return DateTime.Day;
                    case DatePartDayOfWeek:
                        return (int)DayOfWeek;
                    default:
                        throw new ArgumentException();
                }
            }
            catch (ArgumentOutOfRangeException) { }

            if (NetStart < this.AdjustedTicks)
            {
                BigInteger ticks = AdjustedTicks - NetStart;
                // n = number of days since 1/1/0001
                int n = (int)(ticks / TicksPerDay);
                // y400 = number of whole 400-year periods since 1/1/0001
                int y400 = n / DaysPer400Years;
                // n = day number within 400-year period
                n -= y400 * DaysPer400Years;
                // y100 = number of whole 100-year periods within 400-year period
                int y100 = n / DaysPer100Years;
                // Last 100-year period has an extra day, so decrement result if 4
                if (y100 == 4) y100 = 3;
                // n = day number within 100-year period
                n -= y100 * DaysPer100Years;
                // y4 = number of whole 4-year periods within 100-year period
                int y4 = n / DaysPer4Years;
                // n = day number within 4-year period
                n -= y4 * DaysPer4Years;
                // y1 = number of whole years within 4-year period
                int y1 = n / DaysPerYear;
                // Last year has an extra day, so decrement result if 4
                if (y1 == 4) y1 = 3;
                // If year was requested, compute and return it
                if (part == DatePartYear)
                {
                    return y400 * 400 + y100 * 100 + y4 * 4 + y1 + 1;
                }
                // n = day number within year
                n -= y1 * DaysPerYear;
                // If day-of-year was requested, return it
                if (part == DatePartDayOfYear) return n + 1;
                // Leap year calculation looks different from IsLeapYear since y1, y4,
                // and y100 are relative to year 1, not year 0
                bool leapYear = y1 == 3 && (y4 != 24 || y100 == 3);
                int[] days = leapYear ? DaysToMonth366 : DaysToMonth365;
                // All months have less than 32 days, so n >> 5 is a good conservative
                // estimate for the month
                int m = n >> 5 + 1;
                // m = 1-based month number
                try
                {
                    while (n >= days[m]) m++;
                }
                catch (IndexOutOfRangeException)
                {
                    m = 13;
                }
                // If month was requested, return it
                if (part == DatePartMonth) return m;
                // Return 1-based day-of-month
                return n - days[m - 1] + 1;
            }
            else
            {
                BigInteger ticks = AdjustedTicks - NetStart + (DaysPer400Years * TicksPerDay * 25);
                // n = number of days since 1/1/0001
                int n = (int)(ticks / TicksPerDay);
                // y400 = number of whole 400-year periods since 1/1/0001
                int y400 = n / DaysPer400Years;
                // n = day number within 400-year period
                n -= y400 * DaysPer400Years;
                // y100 = number of whole 100-year periods within 400-year period
                int y100 = n / DaysPer100Years;
                // Last 100-year period has an extra day, so decrement result if 4
                if (y100 == 4) y100 = 3;
                // n = day number within 100-year period
                n -= y100 * DaysPer100Years;
                // y4 = number of whole 4-year periods within 100-year period
                int y4 = n / DaysPer4Years;
                // n = day number within 4-year period
                n -= y4 * DaysPer4Years;
                // y1 = number of whole years within 4-year period
                int y1 = n / DaysPerYear;
                // Last year has an extra day, so decrement result if 4
                if (y1 == 4) y1 = 3;
                // If year was requested, compute and return it
                if (part == DatePartYear)
                {
                    int y = y400 * 400 + y100 * 100 + y4 * 4 + y1 - 10000;
                    //Console.WriteLine(y);
                    //////throw new NotImplementedException();
                    return y;
                }
                // n = day number within year
                n -= y1 * DaysPerYear;
                // If day-of-year was requested, return it
                if (part == DatePartDayOfYear) return n + 1;
                // Leap year calculation looks different from IsLeapYear since y1, y4,
                // and y100 are relative to year 1, not year 0
                bool leapYear = y1 == 3 && (y4 != 24 || y100 == 3);
                int[] days = leapYear ? DaysToMonth366 : DaysToMonth365;
                // All months have less than 32 days, so n >> 5 is a good conservative
                // estimate for the month
                int m = n >> 5 + 1;
                // m = 1-based month number
                try
                {
                    while (n >= days[m]) m++;
                }
                catch (IndexOutOfRangeException)
                {
                    m = 13;
                }
                // If month was requested, return it
                if (part == DatePartMonth) return m;
                // Return 1-based day-of-month
                return n - days[m - 1] + 1;
            }


        }

        private static int Modul(int i, int v)
        {
            if (i > 0)
            {
                return i % v;
            }
            int t = i / v;
            t--;
            return Modul(i - t * v, v);
        }



        internal BigInteger GetTicks()
        {
            return this.Atomic._ticks;
        }

        //internal StarDate SpecifyKind(StarDate starDate, object local)
        //{
        //    ////throw new NotImplementedException();
        //}

        //private bool Sol => this.TimeZone.Sol;

        public StarDate addtimezone(string prim)
        {
            StarZone timezone = StarZone.FindTimeZone(prim);
            return this.addtimezone(timezone);
        }

        private StarDate addtimezone(StarZone timezone)
        {
            StarDate dt = this;
            dt.TimeZone = TimeZone;
            return dt;
        }

        public StarDate addtime(string prim)
        {
            Time time = Time.Parse(prim);
            return addtime(time);
        }

        public StarDate addtime(Time time)
        {
            return this + time;
        }

        internal static string textform(long input)
        {
            string suffix;
            long end = input % 100;
            long ten = 10;
            if ((end / ten) == 1)
            {
                suffix = "th";
            }
            else
            {
                end %= 10;
                switch (end)
                {
                    case 1:
                        suffix = "st";
                        break;
                    case 2:
                        suffix = "nd";
                        break;
                    case 3:
                        suffix = "rd";
                        break;
                    default:
                        suffix = "th";
                        break;
                }
            }

            return (input + suffix);
        }

        internal static string textform(int input)
        {
            string suffix;
            int end = input % 100;
            int ten = 10;
            if ((end / ten) == 1)
            {
                suffix = "th";
            }
            else
            {
                end %= 10;
                switch (end)
                {
                    case 1:
                        suffix = "st";
                        break;
                    case 2:
                        suffix = "nd";
                        break;
                    case 3:
                        suffix = "rd";
                        break;
                    default:
                        suffix = "th";
                        break;
                }
            }

            return (input + suffix);

            //MannicDay[] YearArray = MannicYear(Year, 1);

        }

        public bool isleapyear()
        {
            return LeapLevel((long)Year) > 0;
        }

        public bool isDoubleLeapYear()
        {
            return LeapLevel((long)Year) == 2;
        }

        public int LeapLevel()
        {
            return LeapLevel((long)Year);
        }

        public static int LeapLevel(int year)
        {
            return LeapLevel((long)year);
        }

        public static int HorusLength(int year)
        {
            int[] vs = new int[] { 0, 7, 14 };
            return vs[LeapLevel(year)];
        }

        public int HorusLength()
        {
            int[] vs = new int[] { 0, 7, 14 };
            return vs[LeapLevel()];
        }


        public static int LeapLevel(long year)
        {
            if (year % 76 == 0)
            {
                return 2;
            }
            else if (year % 6 == 0)
            {
                return 1;
            }
            else
            {
                return 0;
            }
        }

        private static int LeapDays(int value)
        {
            int[] vs = new int[] { 0, 7, 14 };
            return vs[LeapLevel((long)value)];
        }

        public static StarDate FromGreg(int year)
        {
            return FromGreg(year, 1);
        }

        public static StarDate FromGreg(int year, int month)
        {
            return FromGreg(year, month, 1);
        }

        public static StarDate FromGreg(int year, int month, int day)
        {
            return FromGreg(year, month, day, 0);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour)
        {
            return FromGreg(year, month, day, hour, 0);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min)
        {
            return FromGreg(year, month, day, hour, min, 0);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min, int sec)
        {
            return FromGreg(year, month, day, hour, min, sec, 0);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min, int sec, int mil)
        {
            try
            {
                return new StarDate(new DateTime(year, month, day, hour, min, sec, mil));
            }
            catch (System.ArgumentOutOfRangeException)
            {
                return MathFromGreg(year, month, day, hour, min, sec, mil);
            }
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min, int sec, int mil, int ticks)
        {
            return FromGreg(year, month, day, hour, min, sec, mil).AddTicks(ticks);
        }

        private static StarDate MathFromGreg(int year, int month, int day, int hour, int min, int sec, int mil)
        {
            //////////////Console.WriteLine(Year + " " + Month + " " + day + " " + hour + " " + sec + " " + mil);
            // Number of days in a non-leap Year
            int DaysPerYear = 365;
            // Number of days in 4 years
            int DaysPer4Years = DaysPerYear * 4 + 1;       // 1461
                                                           // Number of days in 100 years
            int DaysPer100Years = DaysPer4Years * 25 - 1;  // 36524
                                                           // Number of days in 400 years
            int DaysPer400Years = DaysPer100Years * 4 + 1; // 146097
            int[] DaysToMonth365 = {
                    0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
            int[] DaysToMonth366 = {
                    0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};
            bool leapyear = GregLeap(year);
            int[] timespans = GregSpans(year);
            StarDate output = new StarDate(ADStart.Atomic);
            output += timespans[0] * DaysPer400Years * StarDate.DayTime;
            output += timespans[1] * DaysPer100Years * StarDate.DayTime;
            output += timespans[2] * DaysPer4Years * StarDate.DayTime;
            output += timespans[3] * DaysPerYear * StarDate.DayTime;
            int days;
            if (leapyear)
            {
                days = DaysToMonth366[month - 1];
            }
            else
            {
                days = DaysToMonth365[month - 1];
            }
            days += day - 1;
            //////////////Console.WriteLine(days);
            output += days * StarDate.DayTime;
            output += hour * StarDate.HourTime;
            output += min * StarDate.MinuteTime;
            output += sec * StarDate.SecondTime;
            output += mil * StarDate.MillisecondTime;
            return output;
            //////throw new NotImplementedException();
        }

        public int GregYear
        {
            get
            {
                return GregDatePart(DatePartYear);
            }

            set
            {
                StarDate dt = StarDate.FromGreg(value, GregMonth, GregDay, Hour, Minute, Second, Millisecond, ExtraTicks);
                this.AdjustedTicks = dt.Ticks;
            }
        }

        public int GregDayOfYear
        {
            get
            {
                return GregDatePart(DatePartDayOfYear);
            }

            set
            {
                StarDate dt = StarDate.FromGreg(value, GregMonth, GregDay, Hour, Minute, Second, Millisecond, ExtraTicks);
                this.AdjustedTicks = dt.Ticks;
            }
        }

        public int GregMonth
        {
            get
            {
                return GregDatePart(DatePartMonth);
            }

            set
            {
                StarDate dt = StarDate.FromGreg(GregYear, value, GregDay, Hour, Minute, Second, Millisecond, ExtraTicks);
                this.AdjustedTicks = dt.Ticks;
            }
        }
        public int GregDay
        {
            get
            {
                return GregDatePart(DatePartDay);
            }

            set
            {
                StarDate dt = StarDate.FromGreg(GregYear, GregMonth, value, Hour, Minute, Second, Millisecond, ExtraTicks);
                this.AdjustedTicks = dt.Ticks;
            }
        }

        public static bool GregLeap(int year)
        {
            if (year < 1)
            {
                year++;
            }

            if (year % 400 == 0)
            {
                return true;
            }
            else if (year % 100 == 0)
            {
                return false;
            }
            else if (year % 4 == 0)
            {
                return true;
            }
            else
            {
                return false;
            }
        }



        internal static int[] GregSpans(int year)
        {
            if (year < 1)
            {
                year++;
            }
            int quent;
            int qmod;
            if (year <= 0)
            {
                quent = year / 400;
                qmod = year % 400;
            }
            else
            {
                quent = year / 400;
                qmod = year % 400;
                if (qmod != 0)
                {
                    quent--;
                }
            }

            ////////////Console.WriteLine" 400mod = " + quent);
            ////////////Console.WriteLine" 400count = " + qmod);
            int centcount = qmod / 100;
            qmod %= 100;
            ////////////Console.WriteLine" centcount = " + centcount);
            int leapcount = qmod / 4;
            qmod %= 4;
            int yearcount = qmod;
            ////////////Console.WriteLine" q " + qmod + " c +" + centcount + " l +" + leapcount + " y +" + yearcount);
            //////////////Console.WriteLine(" ");
            return new int[] { quent, centcount, leapcount, yearcount };
        }


        //public static DateTime GregChineseNewYear(DateTime now)
        //{
        //    System.Globalization.Calendar Chinese = new ChineseLunisolarCalendar();
        //    int i = now.Year;
        //    DateTime h = new DateTime(i, 4, 1);
        //    int ChinaYear = Chinese.GetYear(now);
        //    DateTime Hanukkah = new DateTime(ChinaYear, 1, 1, new ChineseLunisolarCalendar());
        //    return Hanukkah;
        //}

        //public static DateTime GregChineseNewYear()
        //{
        //    return GregChineseNewYear(DateTime.Now);
        //}


        //public static StarDate StarPurim()
        //{
        //    return new StarDate(GregPurim());
        //}

        //public static StarDate StarPurim(DateTime dt)
        //{
        //    return new StarDate(GregPurim(dt));
        //}

        //public static StarDate StarPurim(StarDate dt)
        //{
        //    return new StarDate(GregPurim(dt));
        //}

        //public static DateTime GregPurim()
        //{
        //    return GregPurim(DateTime.Now);
        //}

        //public static DateTime GregPurim(DateTime now)
        //{
        //    System.Globalization.Calendar HebCal = new HebrewCalendar();
        //    int i = now.Year;
        //    DateTime h = new DateTime(i, 11, 1);
        //    int hebyear = HebCal.GetYear(now);
        //    DateTime Purim = new DateTime(hebyear, 6, 14, new HebrewCalendar());
        //    return Purim;
        //}

        //public static DateTime GregPurim(StarDate dt)
        //{
        //    DateTime o = new StarDate(dt.Year, 12, 1).DateTime;
        //    return GregPurim(o);
        //}

        // Constructs a StarDate from a tick count. The _ticks
        // argument specifies the date as the number of 100-nanosecond intervals
        // that have elapsed since 1/1/0001 12:00am.
        //
        public StarDate(BigInteger ticks)
        {
            internalTicks = ticks;
            _timeZone = StarZone.Local;
            accuracy = 0;
        }

        public StarDate(BigInteger ticks, Accuracy error)
        {
            internalTicks = ticks;
            accuracy = error;
            _timeZone = StarZone.Local;
        }

        public StarDate(BigInteger ticks, StarZone zone)
        {
            internalTicks = ticks;
            _timeZone = zone;
            accuracy = 0;
        }

        public StarDate(BigInteger ticks, Accuracy error, StarZone zone)
        {
            internalTicks = ticks;
            accuracy = error;
            _timeZone = zone;
        }

        public StarDate(BigInteger ticks, DateTimeKind kind)
        {
            this.internalTicks = ticks;
            this.accuracy = 0;
            if (kind == DateTimeKind.Local)
            {
                this._timeZone = Local;
            }
            else if (kind == DateTimeKind.Utc)
            {
                this._timeZone = UTC;
            }
            else
            {
                this._timeZone = UnspecifiedTimeZone;
            }
        }

        public StarDate(BigInteger ticks, Accuracy error, DateTimeKind kind) : this(ticks, kind)
        {
            this.accuracy = error;
        }

        public StarDate(BigInteger ticks, TimeSpan Offset) : this(ticks, (Time)Offset)
        {

        }

        public StarDate(BigInteger ticks, Time Offset)
        {
            internalTicks = ticks;
            accuracy = Accuracy.Tick;
            _timeZone = StarZone.GetStarZoneFromOffset(ticks, Offset);
        }





        // Constructs a StarDate from a given Year, month, and day. The
        // time-of-day of the resulting StarDate is always midnight.
        //

        public StarDate(long year) : this(year, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(long year, StarZone zone) : this(year, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, zone)
        {

        }


        public StarDate(long year, long month) : this(year, month, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(long year, long month, StarZone zone) : this(year, month, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, zone)
        {

        }

        public StarDate(long year, long month, long day) : this(year, month, day, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(long year, long month, long day, StarZone timezone) : this(year, month, day, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, timezone)
        {

        }

        public StarDate(long year, long month, long day, long hour) : this(year, month, day, hour, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(long year, long month, long day, long hour, StarZone timezone) : this(year, month, day, hour, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, timezone)
        {

        }

        public StarDate(long year, long month, long day, long hour, long minute) : this(year, month, day, hour, minute, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(long year, long month, long day, long hour, long minute, StarZone timezone) : this(year, month, day, hour, minute, PlaceHolder, PlaceHolder, PlaceHolder, timezone)
        {

        }


        public StarDate(long year, long month, long day, long hour, long minute, long second) : this(year, month, day, hour, minute, second, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(long year, long month, long day, long hour, long minute, long second, StarZone timezone) : this(year, month, day, hour, minute, second, PlaceHolder, PlaceHolder, timezone)
        {

        }


        public StarDate(long year, long month, long day, long hour, long minute, long second, long millisecond) : this(year, month, day, hour, minute, second, millisecond, PlaceHolder, Local)
        {

        }

        public StarDate(long year, long month, long day, long hour, long minute, long second, long millisecond, StarZone timezone) : this(year, month, day, hour, minute, second, millisecond, PlaceHolder, timezone)
        {

        }

        public StarDate(long year, long month, long day, long hour, long minute, long second, long millisecond, long ticks) : this(year, month, day, hour, minute, second, millisecond, ticks, Local)
        {

        }

        public StarDate(long year, long month, long day, long hour, long minute, long second, long millisecond, long ticks, StarZone timezone)
        {
            //if ((year > 1900) && (year < 2100))
            //{
            //    year += 10000;
            //}
            //base constructor used to generate all dates from standard digits
            _timeZone = timezone;
            internalTicks = Manu.Ticks;
            accuracy = Accuracy.Year; //Year
            //adjusting for timezone
            //subtract datetime offset because internal ticks refer to UTC Atomic time
            if (_timeZone.SupportsDaylightSavingTime)
            {
                internalTicks -= _timeZone.GetUtcOffset(internalTicks);
            }
            else
            {
                internalTicks += _timeZone.BaseUtcOffset.Ticks;
            }
            if (year < 1000000)
            {
                int y100k = (int)(year / 100000);
                year -= y100k * 100000;
                int y78 = (int)(year / 78);
                year -= y78 * 78;
                int y6 = (int)(year / 6);
                year -= y6 * 6;
                internalTicks += y78 * TicksPerSeventyEightYears;
                internalTicks += y6 * TicksPerSixYears;
                internalTicks += year * TicksPerYear;
            }
            else
            {
                int y78 = (int)(year / 78);
                year -= y78 * 78;
                int y6 = (int)(year / 6);
                year -= y6 * 6;
                internalTicks += y78 * TicksPerSeventyEightYears;
                internalTicks += y6 * TicksPerSixYears;
                internalTicks += year * TicksPerYear;
            }
            if (!isvalidhorus(year, month, day))
            {
                throw new ArgumentOutOfRangeException("Invalid Leap Year");
            }
            else if (month == PlaceHolder)
            {

            }
            else if (month < 1 || month > 14)
            {
                throw new ArgumentOutOfRangeException("Month");
            }
            else
            {
                Accuracy++; //Month
                internalTicks += (month - 1) * TicksPerMonth;
                if (day == PlaceHolder)
                {
                    //accuracy = Accuracy.Month;
                }
                else if (day < 1 || day > 28)
                {
                    throw new ArgumentOutOfRangeException("Day");
                }
                else
                {
                    int d = (int)(day - 1);
                    internalTicks += TicksPerDay * d;
                    Accuracy++; //Day
                    if (hour == PlaceHolder)
                    {
                        //accuracy = Accuracy.Day;
                    }
                    else if (hour < 0 || hour > 30)
                    {
                        throw new ArgumentOutOfRangeException("Hour");
                    }
                    else
                    {
                        Accuracy++; //Hour
                        internalTicks += hour * TicksPerHour;
                        if (minute == PlaceHolder)
                        {
                            //accuracy = Accuracy.Hour;
                        }
                        else if (minute < 0 || minute > 59)
                        {
                            throw new ArgumentOutOfRangeException("Minute");
                        }
                        else
                        {
                            internalTicks += minute * TicksPerMinute;
                            Accuracy++; //Minute
                            if (second == PlaceHolder)
                            {
                                //accuracy = Accuracy.Second;
                                //internalTicks += accuracy;
                            }
                            else if (second < 0 || second > 60)
                            {
                                throw new ArgumentOutOfRangeException("second");
                            }
                            else
                            {
                                Accuracy++; //Second
                                if (second == 60)
                                {
                                    if (StarDate.LeapSeconds(internalTicks, year, month, day, hour, minute, second, DateTimeKind.Unspecified))
                                    {
                                        // if we have leap second (second = 60) then we'll need to check if it is valid time.
                                        // if it is valid, then we adjust the second to 59 so DateTime will consider this second is last second
                                        // in the specified minute.
                                        // if it is not valid time, we'll eventually throw.
                                        second = 59;
                                    }
                                    else
                                    {
                                        throw new ArgumentOutOfRangeException("second");
                                    }
                                }
                                internalTicks += second * TicksPerSecond;
                                if (millisecond == PlaceHolder)
                                {
                                    accuracy = Accuracy.Second;
                                }
                                else if (millisecond < 0 || millisecond > 1000)
                                {
                                    throw new ArgumentOutOfRangeException("millisecond");
                                }
                                else
                                {
                                    Accuracy++; //Millisecond
                                    if (ticks == PlaceHolder)
                                    {
                                        accuracy = Accuracy.Millisecond;
                                    }
                                    else if (ticks < 0 || ticks > 10000)
                                    {
                                        throw new ArgumentOutOfRangeException("ticks");
                                    }
                                    else
                                    {
                                        Accuracy++; //Ticks
                                        internalTicks += ticks;
                                        accuracy = Accuracy.Tick;
                                    }
                                }

                            }

                        }

                    }

                }
            }
        }

        private static bool LeapSeconds(BigInteger dateData, long year, long month, long day, long hour, long minute, long second, DateTimeKind unspecified)
        {
            DateTime dt = new DateTime((long)(dateData - Manu.Ticks)).Date;
            year = dt.Year;
            month = dt.Month;
            day = dt.Day;
            try
            {
                DateTime test = new DateTime((int)year, (int)month, (int)day, (int)hour, (int)minute, (int)second);
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }

        internal static bool IsValidDay(long year, long month, long day, long era)
        {
            throw new NotImplementedException();
        }

        private static bool isvalidhorus(long year, long month, long day)
        {
            if (month == 14)
            {
                int v = LeapLevel((long)year);
                switch (v)
                {
                    case 0:
                        return false;
                    case 1:
                    case 2:
                    default:
                        return day <= 7 * v;
                }
            }
            else
            {
                return true;
            }
        }

        internal static StarDate fromdigits(StarZone z, long year, long month, long day, long hour, long min, long second, long millisecond, long ticks)
        {
            StarDate dt = Manu;
            int y78 = (int)(year / 78);
            year -= y78 * 78;
            int y6 = (int)(year / 6);
            year -= y6 * 6;
            dt += y78 * Seventy_Eight;
            dt += y6 * Sixyear;
            dt += year * YearTime;
            dt += month * StarDate.MonthTime;
            dt += day * StarDate.DayTime;
            dt += hour * StarDate.HourTime;
            dt += min * StarDate.MinuteTime;
            dt += second * StarDate.SecondTime;
            dt += millisecond * StarDate.MillisecondTime;
            dt += new Time(ticks);
            dt -= z.Offset(dt);
            //////throw new NotImplementedException();
            return dt;
        }

        public StarDate(long year, long month, long day, long hour, long minute, long second, long millisecond, long ticks, Accuracy error) : this(year, month, day, hour, minute, second, millisecond, ticks, Local)
        {
            this.accuracy = error;
        }

        public StarDate(long year, long month, long day, long hour, long minute, long second, long millisecond, long ticks, Accuracy error, StarZone uTC) : this(year, month, day, hour, minute, second, millisecond, ticks, uTC)
        {
            this.accuracy = error;
        }

        public StarDate(DateTime dt)
        {
            internalTicks = NetStart + dt.Ticks;
            accuracy = Accuracy.Tick;
            if (dt.Kind == DateTimeKind.Local)
            {
                this._timeZone = Local;
                internalTicks -= Local.Offset(dt).Ticks;
            }
            else if (dt.Kind == DateTimeKind.Utc)
            {
                this._timeZone = UTC;
            }
            else
            {
                this._timeZone = UnspecifiedTimeZone;
            }

        }

        public StarDate(DateTime dt, StarZone zone)
        {
            internalTicks = dt.Ticks + NetStart;
            _timeZone = zone;
            accuracy = Accuracy.Tick;
            if (dt.Kind != DateTimeKind.Utc)
            {
                internalTicks -= zone.Offset(dt);
            }
        }

        public StarDate(DateTime dt, Accuracy margin, StarZone zone) : this(dt, zone)
        {
            Accuracy = margin;
        }

        public StarDate(DateTime dt, Time offset) : this(dt, (TimeSpan)offset)
        {

        }

        public StarDate(DateTime dt, TimeSpan offset) : this(new DateTimeOffset(dt, offset))
        {

        }


        public StarDate(DateTimeOffset dt)
        {
            if (dt.Offset == Local.Offset(dt.Date))
            {
                _timeZone = Local;
            }
            else
            {
                _timeZone = StarZone.GetStarZoneFromOffset(dt.UtcDateTime.Ticks + NetStart, (Time)dt.Offset);
            }
            internalTicks = dt.Ticks;
            accuracy = Accuracy.Tick;
        }

        public StarDate(Time t) : this()
        {
            this.Atomic = t;
        }

        public StarDate(string basic) : this(StarDate.Parse(basic))
        {

        }

        internal StarDate(StarDate dt)
        {
            this.internalTicks = dt.internalTicks;
            this.accuracy = dt.accuracy;
            this._timeZone = dt.TimeZone;
        }


        public StarDate(Time t, StarZone zone) : this(t)
        {
            this.Atomic = t;
            this.TimeZone = zone;
        }

        public StarDate(int[] vs) : this(vs[0], vs[1], vs[2], vs[3], vs[4], vs[5], vs[6], vs[7])
        {
        }

        public StarDate(int[] vs, Accuracy error1, StarZone timezone) : this(vs, timezone)
        {
            this.accuracy = error1;
            this._timeZone = timezone;
        }

        //public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks, Accuracy error1, StarZone timezone) : this(year, month, day, hour, minute, second, millisecond, ticks)
        //{
        //    this.accuracy = error1;
        //    TimeZone = timezone;
        //}

        public StarDate(int[] vs, StarZone timezone) : this(vs[0], vs[1], vs[2], vs[3], vs[4], vs[5], vs[6], vs[7], timezone)
        {
        }

        public StarDate(BigInteger ticks, DateTimeKind kind, bool isAmbiguousLocalDst) : this(ticks, kind)
        {
        }

        private StarZone fromDateTimeKind(DateTimeKind kind)
        {
            switch (kind)
            {
                case DateTimeKind.Local:
                    return Local;
                case DateTimeKind.Utc:
                    return UTC;
                case DateTimeKind.Unspecified:
                default:
                    return UnspecifiedTimeZone;
            }
        }

        // Returns the StarDate resulting from adding the given
        // TimeSpan to this StarDate.
        //
        public StarDate Add(TimeSpan value)
        {
            return AddTicks(value.Ticks);
        }

        public StarDate Add(Time value)
        {
            return AddTicks(value.Ticks);
        }

        public StarDate AddTicks(BigInteger ticks)
        {
            StarDate dt = this;
            dt.internalTicks += ticks;
            return dt;
        }

        // Returns the StarDate resulting from adding a fractional number of
        // time units to this StarDate.
        private StarDate Add(double value, int scale)
        {
            long millis = (long)(value * scale + (value >= 0 ? 0.5 : -0.5));
            if (millis <= -MaxMillis || millis >= MaxMillis)
                throw new ArgumentOutOfRangeException(); //("value", ); //Environment.GetResourceString("ArgumentOutOfRange_AddValue"));
            return AddTicks(millis * TicksPerMillisecond);
        }

        private StarDate Add(double value, long scale)
        {
            long millis = (long)(value * scale + (value >= 0 ? 0.5 : -0.5));
            if (millis <= -MaxMillis || millis >= MaxMillis)
                throw new ArgumentOutOfRangeException(); //("value", ); //Environment.GetResourceString("ArgumentOutOfRange_AddValue"));
            return AddTicks(millis * TicksPerMillisecond);
        }

        // Returns the StarDate resulting from adding the given number of
        // years to this StarDate. The result is computed by incrementing
        // (or decrementing) the Year part of this StarDate by value
        // years. If the month and day of this StarDate is 2/29, and if the
        // resulting Year is not a leap Year, the month and day of the resulting
        // StarDate becomes 2/28. Otherwise, the month, day, and time-of-day
        // parts of the result are the same as those of this StarDate.
        //
        public StarDate AddYears(double value)
        {
            if (value % 1 == 0)
            {
                return AddYears((int)value);
            }
            else
            {
                return Add(value, MillisPerYear);
            }
        }

        public StarDate AddYears(int value)
        {
            StarDate sd = this;
            sd.Year += value;
            return sd;
        }



        // Returns the StarDate resulting from adding the given number of
        // months to this StarDate. The result is computed by incrementing
        // (or decrementing) the Year and month parts of this StarDate by
        // months months, and, if required, adjusting the day part of the
        // resulting date downwards to the last day of the resulting month in the
        // resulting Year. The time-of-day part of the result is the same as the
        // time-of-day part of this StarDate.
        //
        // In more precise terms, considering this StarDate to be of the
        // form y / m / d + t, where y is the
        // Year, m is the month, d is the day, and t is the
        // time-of-day, the result is y1 / m1 / d1 + t,
        // where y1 and m1 are computed by adding months months
        // to y and m, and d1 is the largest value less than
        // or equal to d that denotes a valid day in month m1 of Year
        // y1.
        //
        public StarDate AddMonths(double months)
        {
            return Add(months, MillisPerMonth);
        }

        public StarDate AddWeeks(double value)
        {
            return Add(value, MillisPerWeek);
        }

        // Returns the StarDate resulting from adding a fractional number of
        // days to this StarDate. The result is computed by rounding the
        // fractional number of days given by value to the nearest
        // millisecond, and adding that interval to this StarDate. The
        // value argument is permitted to be negative.
        //

        public StarDate AddDays(double value)
        {
            return Add(value, MillisPerDay);
        }



        // Returns the StarDate resulting from adding a fractional number of
        // hours to this StarDate. The result is computed by rounding the
        // fractional number of hours given by value to the nearest
        // millisecond, and adding that interval to this StarDate. The
        // value argument is permitted to be negative.
        //
        public StarDate AddHours(double value)
        {
            return Add(value, MillisPerHour);
        }

        // Returns the StarDate resulting from adding a fractional number of
        // minutes to this StarDate. The result is computed by rounding the
        // fractional number of minutes given by value to the nearest
        // millisecond, and adding that interval to this StarDate. The
        // value argument is permitted to be negative.
        //
        public StarDate AddMinutes(double value)
        {
            return Add(value, MillisPerMinute);
        }

        // Returns the StarDate resulting from adding a fractional number of
        // seconds to this StarDate. The result is computed by rounding the
        // fractional number of seconds given by value to the nearest
        // millisecond, and adding that interval to this StarDate. The
        // value argument is permitted to be negative.
        //
        public StarDate AddSeconds(double value)
        {
            return Add(value, MillisPerSecond);
        }

        // Returns the StarDate resulting from the given number of
        // milliseconds to this StarDate. The result is computed by rounding
        // the number of milliseconds given by value to the nearest integer,
        // and adding that interval to this StarDate. The value
        // argument is permitted to be negative.
        //
        public StarDate AddMilliseconds(double value)
        {
            return Add(value, 1);
        }







        // Returns the StarDate resulting from adding the given number of
        // 100-nanosecond _ticks to this StarDate. The value argument
        // is permitted to be negative.
        //
        public StarDate AddTicks(long value)
        {
            BigInteger ticks = internalTicks;
            return new StarDate((ticks + value), accuracy, TimeZone);
        }



        // Compares two StarDate values, returning an integer that indicates
        // their relationship.
        //
        public static int Compare(StarDate t1, StarDate t2)
        {
            BigInteger ticks1 = t1.internalTicks;
            BigInteger ticks2 = t2.internalTicks;
            if (ticks1 > ticks2) return 1;
            if (ticks1 < ticks2) return -1;
            return 0;
        }

        // Compares this StarDate to a given object. This method provides an
        // implementation of the IComparable interface. The object
        // argument must be another StarDate, or otherwise an exception
        // occurs.  Null is considered less than any instance.
        //
        // Returns a value less than zero if this  object
        public int CompareTo(Object value)
        {
            if (value == null) return 1;
            if (!(value is StarDate))
            {
                throw new ArgumentException(); //); //Environment.GetResourceString("Arg_MustBeStarDate"));
            }

            BigInteger valueTicks = ((StarDate)value).Ticks;
            BigInteger ticks = Ticks;
            if (ticks > valueTicks) return 1;
            if (ticks < valueTicks) return -1;
            return 0;
        }

        public int CompareTo(StarDate value)
        {
            BigInteger valueTicks = value.Ticks;
            BigInteger ticks = Ticks;
            if (ticks > valueTicks) return 1;
            if (ticks < valueTicks) return -1;
            return 0;
        }

        // Returns the tick count corresponding to the given Year, month, and day.
        // Will check the if the parameters are valid.
        private static BigInteger DateToTicks(int year, int month, int day)
        {
            return new StarDate(year, month, day).Ticks;
        }

        // Return the tick count corresponding to the given hour, minute, second.
        // Will check the if the parameters are valid.
        private static long TimeToTicks(int hour, int minute, int second)
        {
            //TimeSpan.TimeToTicks is a family access function which does no error checking, so
            //we need to put some error checking out here.
            if (hour >= 0 && hour < 24 && minute >= 0 && minute < 60 && second >= 0 && second < 60)
            {
                return (Time.TimeToTicks(hour, minute, second));
            }
            throw new ArgumentOutOfRangeException(); //(null, ); //Environment.GetResourceString("ArgumentOutOfRange_BadHourMinuteSecond"));
        }



        // Converts an OLE Date to a tick count.
        // This function is duplicated in COMStarDate.cpp
        internal static long DoubleDateToTicks(double value)
        {
            // The check done this way will take care of NaN
            if (!(value < OADateMaxAsDouble) || !(value > OADateMinAsDouble))
                throw new ArgumentException(); //); //Environment.GetResourceString("Arg_OleAutDateInvalid"));

            // Conversion to long will not cause an overflow here, as at this point the "value" is in between OADateMinAsDouble and OADateMaxAsDouble
            long millis = (long)(value * MillisPerDay + (value >= 0 ? 0.5 : -0.5));
            // The interesting thing here is when you have a value like 12.5 it all positive 12 days and 12 hours from 01/01/1899
            // However if you a value of -12.25 it is minus 12 days but still positive 6 hours, almost as though you meant -11.75 all negative
            // This line below fixes up the millis in the negative case
            if (millis < 0)
            {
                millis -= (millis % MillisPerDay) * 2;
            }

            millis += DoubleDateOffset / TicksPerMillisecond;

            if (millis < 0 || millis >= MaxMillis) throw new ArgumentException(); //); //Environment.GetResourceString("Arg_OleAutDateScale"));
            return millis * TicksPerMillisecond;
        }

        //#if !FEATURE_CORECLR
        //        [DllImport(JitHelpers.QCall, CharSet = CharSet.Unicode)]
        //        [SecurityCritical]
        //        [ResourceExposure(ResourceScope.Tick)]
        //        [SuppressUnmanagedCodeSecurity]
        //        [return: MarshalAs(UnmanagedType.Bool)]
        //        internal static extern bool LegacyParseMode();

        //        [DllImport(JitHelpers.QCall, CharSet = CharSet.Unicode)]
        //        [SecurityCritical]
        //        [ResourceExposure(ResourceScope.Tick)]
        //        [SuppressUnmanagedCodeSecurity]
        //        [return: MarshalAs(UnmanagedType.Bool)]
        //        internal static extern bool EnableAmPmParseAdjustment();
        //#endif

        // Checks if this StarDate is equal to a given object. Returns
        // true if the given object is a boxed StarDate and its value
        // is equal to the value of this StarDate. Returns false
        // otherwise.
        //
        public override bool Equals(Object value)
        {
            if (value is StarDate)
            {
                return this.Equals((StarDate)value);
            }
            return false;
        }

        public bool Equals(StarDate value)
        {
            return internalTicks == value.internalTicks;
        }

        // Compares two StarDate values for equality. Returns true if
        // the two StarDate values are equal, or false if they are
        // not equal.
        //
        public static bool Equals(StarDate t1, StarDate t2)
        {
            return t1.Equals(t2);
        }



        public static StarDate FromBinary(Int64 dateData)
        {
            return DateTime.FromBinary(dateData);
        }

        // A version of ToBinary that uses the real representation and does not adjust local times. This is needed for
        // scenarios where the serialized data must maintain compatability
        internal static StarDate FromBinaryRaw(Int64 dateData)
        {
            BigInteger ticks = dateData & (Int64)ticksMask;
            if (ticks < MinTicks || ticks > MaxTicks)
                throw new ArgumentException(); //); //Environment.GetResourceString("Argument_StarDateBadBinaryData"), "internalTicks");
            return new StarDate((UInt64)dateData);
        }

        // Creates a StarDate from a Windows filetime. A Windows filetime is
        // a long representing the date and time as the number of
        // 100-nanosecond intervals that have elapsed since 1/1/1601 12:00am.
        //
        private static StarDate FromFileTime(long fileTime)
        {
            return (StarDate)DateTime.FromFileTime(fileTime);
        }

        private static StarDate FromFileTimeUtc(long fileTime)
        {
            return new StarDate(DateTime.FromFileTimeUtc(fileTime));
        }

        // Creates a StarDate from an OLE Automation Date.
        //
        //public static StarDate FromOADate(double d)
        //{
        //    return (StarDate)DateTime.FromOADate(d);
        //}

#if FEATURE_SERIALIZATION
        [System.Security.SecurityCritical /*auto-generated_required*/]
        void ISerializable.GetObjectData(SerializationInfo info, StreamingContext context) {
            if (info==null) {
                throw new ArgumentNullException("info");
            }
            Contract.EndContractBlock();

            // Serialize both the old and the new format
            info.AddValue(TicksField, InternalTicks);
            info.AddValue(DateDataField, dateData);
        }
#endif

        public Boolean IsDaylightSavingTime()
        {
            return TimeZone.IsDaylightSavingTime(this);
        }

        public static StarDate SpecifyKind(StarDate value, DateTimeKind kind)
        {
            value.Kind = kind;
            return value;
        }

        public Int64 ToBinary()
        {
            return DateTime.ToBinary();
        }

        // Return the underlying data, without adjust local times to the right time zone. Needed if performance
        // or compatability are important.
        internal Int64 ToBinaryRaw()
        {
            return (Int64)internalTicks;
        }

        // Returns the hash code for this StarDate.
        //
        public override int GetHashCode()
        {
            BigInteger ticks = internalTicks;
            return unchecked((int)ticks) ^ (int)(ticks >> 32);
        }



        // FullSystemTime struct matches Windows SYSTEMTIME struct, except we added the extra nanoSeconds field to store
        // more precise time.
        [StructLayout(LayoutKind.Sequential)]
        internal struct FullSystemTime
        {
            internal FullSystemTime(int year, int month, DayOfWeek dayOfWeek, int day, int hour, int minute, int second)
            {
                wYear = (ushort)year;
                wMonth = (ushort)month;
                wDayOfWeek = (ushort)dayOfWeek;
                wDay = (ushort)day;
                wHour = (ushort)hour;
                wMinute = (ushort)minute;
                wSecond = (ushort)second;
                wMillisecond = 0;
                hundredNanoSecond = 0;
            }

            internal FullSystemTime(BigInteger ticks)
            {
                StarDate dt = new StarDate(ticks);

                long year, month, day;
                dt.GetDatePart(out year, out month, out day);

                wYear = (ushort)year;
                wMonth = (ushort)month;
                wDayOfWeek = (ushort)dt.DayOfWeek;
                wDay = (ushort)day;
                wHour = (ushort)dt.Hour;
                wMinute = (ushort)dt.Minute;
                wSecond = (ushort)dt.Second;
                wMillisecond = (ushort)dt.Millisecond;
                hundredNanoSecond = 0;
            }

            internal ushort wYear;
            internal ushort wMonth;
            internal ushort wDayOfWeek;
            internal ushort wDay;
            internal ushort wHour;
            internal ushort wMinute;
            internal ushort wSecond;
            internal ushort wMillisecond;
            internal long hundredNanoSecond;
        };

        //[System.Security.SecurityCritical]  // auto-generated
        //[MethodImplAttribute(MethodImplOptions.InternalCall)]
        //internal static extern long GetSystemTimeAsFileTime();

        //[System.Security.SecurityCritical]  // auto-generated
        //[MethodImplAttribute(MethodImplOptions.InternalCall)]
        //internal static extern bool ValidateSystemTime(ref FullSystemTime time, bool localTime);

        //[System.Security.SecurityCritical]  // auto-generated
        //[MethodImplAttribute(MethodImplOptions.InternalCall)]
        //internal static extern void GetSystemTimeWithLeapSecondsHandling(ref FullSystemTime time);

        //[System.Security.SecurityCritical]
        //[ResourceExposure(ResourceScope.Tick)]
        //[DllImport(JitHelpers.QCall, CharSet = CharSet.Unicode), SuppressUnmanagedCodeSecurity]
        //internal static extern bool IsLeapSecondsSupportedSystem();

        //[System.Security.SecurityCritical]  // auto-generated
        //[MethodImplAttribute(MethodImplOptions.InternalCall)]
        //internal static extern bool SystemFileTimeToSystemTime(long fileTime, ref FullSystemTime time);

        //[System.Security.SecurityCritical]  // auto-generated
        //[MethodImplAttribute(MethodImplOptions.InternalCall)]
        //internal static extern bool SystemTimeToSystemFileTime(ref FullSystemTime time, ref long fileTime);

        //[System.Security.SecuritySafeCritical]
        //internal static bool SystemSupportLeapSeconds()
        //{
        //    return IsLeapSecondsSupportedSystem();
        //}

        //[System.Security.SecuritySafeCritical]
        //internal static StarDate InternalFromFileTime(long fileTime)
        //{
        //    FullSystemTime time = new FullSystemTime();
        //    if (SystemFileTimeToSystemTime(fileTime, ref time))
        //    {
        //        time.hundredNanoSecond = fileTime % TicksPerMillisecond;
        //        return CreateStarDateFromSystemTime(ref time);
        //    }

        //    throw new ArgumentOutOfRangeException(); //("fileTime", ); //Environment.GetResourceString("ArgumentOutOfRange_StarDateBadTicks"));
        //}

        //[System.Security.SecuritySafeCritical]
        //internal static long InternalToFileTime(BigInteger ticks)
        //{
        //    long fileTime = 0;
        //    FullSystemTime time = new FullSystemTime(ticks);
        //    if (SystemTimeToSystemFileTime(ref time, ref fileTime))
        //    {
        //        return fileTime + ticks % TicksPerMillisecond;
        //    }

        //    throw new ArgumentOutOfRangeException(); //(null, ); //Environment.GetResourceString("ArgumentOutOfRange_FileTimeInvalid"));
        //}

        // Just in case for any reason CreateStarDateFromSystemTime not get inlined,
        // we are passing time by ref to avoid copying the structure while calling the method.
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        internal static StarDate CreateStarDateFromSystemTime(ref FullSystemTime time)
        {
            BigInteger ticks = DateToTicks(time.wYear, time.wMonth, time.wDay);
            ticks += TimeToTicks(time.wHour, time.wMinute, time.wSecond);
            ticks += time.wMillisecond * TicksPerMillisecond;
            ticks += time.hundredNanoSecond;
            return new StarDate(((UInt64)(ticks)) | KindUtc);
        }


        /// <summary>
        /// Private Properties
        /// </summary>

        internal BigInteger AdjustedTicks
        {
            get
            {
                return internalTicks + Offset.Ticks;
            }
            set
            {
                //a = d + o
                //a - o = d
                internalTicks = value - Offset.Ticks;
            }
        }

        /// <summary>
        /// Properties of StarDates
        /// </summary>

        // Returns the date part of this StarDate. The resulting value
        // corresponds to this StarDate with the time-of-day part set to noon with 12 hours error 
        //


        public StarDate Date
        {
            get
            {
                StarDate dt = this;
                dt.Hour = 12;
                dt.accuracy = Accuracy.Day;
                return dt;
            }
        }

        //returns the margin of error for a time

        //public Time error
        //{
        //    get
        //    {
        //        return new Time(accuracy);
        //    }

        //    private set
        //    {
        //        accuracy = value.Ticks;
        //    }
        //}

        //returns the TimeZone of this date

        public StarZone TimeZone
        {
            get
            {
                if (_timeZone == null)
                {
                    _timeZone = UTC;
                }
                return _timeZone;
            }

            set
            {
                _timeZone = value;
            }
        }

        //gives legacy .NET DateTimeKind

        [Pure]
        public DateTimeKind Kind
        {
            get
            {
                if (TimeZone == Local)
                {
                    return DateTimeKind.Local;
                }
                else if (TimeZone == UTC)
                {
                    return DateTimeKind.Utc;
                }
                else
                {
                    return DateTimeKind.Unspecified;
                }
            }

            private set
            {
                if (value == DateTimeKind.Local)
                {
                    this.TimeZone = Local;
                }
                else if (value == DateTimeKind.Utc)
                {
                    this.TimeZone = UTC;
                }
            }
        }

        public Time LocalDay
        {
            get
            {
                return TimeZone.LocalDay;
            }
        }

        public BigInteger TicksPerLocalDay
        {
            get
            {
                return LocalDay.Ticks;
            }
        }

        //returns true if time zone is on earth

        public bool IsTerran
        {
            get
            {
                return this.TimeZone.IsTerran;
            }
        }

        //returns true if time zone is on earth and has daylight savings time
        public bool SupportsDaylightSavingTime
        {
            get
            {
                return this.TimeZone.SupportsDaylightSavingTime;
            }

        }

        //returns utc offset for this date

        public Time Offset
        {
            get
            {
                if (this.TimeZone.SupportsDaylightSavingTime)
                {
                    return this.TimeZone.Offset(this);
                }
                else
                {
                    return this.TimeZone.BaseUtcOffset;
                }
            }
            set
            {
                if (Offset != value)
                {
                    if (Offset == Local.Offset(this))
                    {
                        TimeZone = Local;
                    }
                    else
                    {
                        TimeZone = StarZone.GetStarZoneFromOffset(internalTicks, value);
                    }
                }
            }
        }

        //returns DateTime equivalent

        public DateTime DateTime
        {
            get
            {
                DateTime dt = new DateTime((long)(internalTicks - NetStart + Offset));
                DateTime.SpecifyKind(dt, Kind);
                return dt;
            }
            set
            {
                Kind = value.Kind;
                AdjustedTicks = value.Ticks + NetStart;
            }
        }

        public DateTime DateTimeUTC
        {
            get
            {
                DateTime dt = new DateTime((long)(internalTicks - NetStart));
                DateTime.SpecifyKind(dt, DateTimeKind.Utc);
                return dt;
            }
            set
            {
                internalTicks = value.Ticks + NetStart;
            }
        }

        public DateTimeOffset DateTimeOffset
        {
            get
            {
                return new DateTimeOffset((long)(internalTicks - NetStart), (TimeSpan)Offset);
            }
            set
            {
                internalTicks = value.Ticks;
                Offset = (Time)value.Offset;
            }
        }

        //public long y100k
        //{
        //    get => GetDatePart(DatePart100k);
        //}

        public long FullYear
        {
            get
            {
                //Contract.Ensures(Contract.Result<int>() >= 1 && Contract.Result<int>() <= 1000000);
                return GetDatePart(DatePartYear);
            }
            set
            {
                StarDate dt = this;
                dt.TimeZone = UTC;
                long[] vs;
                dt.GetDatePart(out vs);
                dt = new StarDate(value, vs[1], vs[2], vs[3], vs[4], vs[5], vs[6], vs[7], UTC);
                dt--;
                this.internalTicks = dt.internalTicks;
            }
        }


        // Returns the Year part of this StarDate. The returned value is an
        // integer between 1 and 1,000,000.

        public int Year
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1 && Contract.Result<int>() <= 1000000);
                return ToManu(FullYear);
            }
            set
            {
                StarDate dt = this;
                dt.TimeZone = UTC;
                int[] vs;
                dt.GetDatePart(out vs);
                dt = new StarDate(value, vs[1], vs[2], vs[3], vs[4], vs[5], vs[6], vs[7], UTC);
                //dt--;
                this.AdjustedTicks = dt.internalTicks;
            }
        }

        private int ToManu(long fullYear)
        {
            return (int)(fullYear % 1000000);
        }



        // Returns the month part of this StarDate. The returned value is an
        // integer between 1 and 12.
        //
        public int Month
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1 && Contract.Result<int>() <= 14);
                return (int)GetDatePart(DatePartMonth);
            }
            set
            {
                Contract.Ensures(value >= 1 && value <= 14);
                if ((value == 14) && (HorusLength() < Day))
                {
                    this.DayOfYear = 1;
                    this.Year++;
                }
                else
                {
                    int diff = value - this.Month;
                    this = this.AddMonths(diff);
                }
            }
        }

        // Returns the week-of-Year part of this StarDate. The returned value
        // is an integer between 1 and 54.
        //

        public int WeekOfYear
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1 && Contract.Result<int>() <= 54);
                return (DayOfYear / 7) + 1;
            }
            set
            {
                Contract.Ensures(value >= 1 && value <= (54));
                int diff = value - this.WeekOfYear;
                this = this.AddWeeks(diff);
            }
        }

        // Returns the day-of-Year part of this StarDate. The returned value
        // is an integer between 1 and 378.
        //
        public int DayOfYear
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1);
                Contract.Ensures(Contract.Result<int>() <= 378);  // leap Year
                return (int)GetDatePart(DatePartDayOfYear);
            }
            set
            {
                Contract.Ensures(value >= 1);
                Contract.Ensures(value <= YearLength());  // leap Year
                int diff = value - this.DayOfYear;
                this = this.AddDays(diff);
            }
        }

        private int YearLength()
        {
            return 364 + HorusLength();
        }

        private void Overflow()
        {
            if (StarDate.acceptoverflow)
            {
                this.internalTicks += TicksPerYear;
                this.DayOfYear = 1;
            }
            else
            {
                throw new ArgumentException();
            }
        }

        // Returns the day-of-month part of this StarDate. The returned
        // value is an integer between 1 and 28.
        //

        public int Day
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1);
                Contract.Ensures(Contract.Result<int>() <= 28);
                return (int)GetDatePart(DatePartDay);
            }
            set
            {
                Contract.Ensures(value >= 1);
                Contract.Ensures(value <= 28);
                if (Month == 14)
                {
                    Contract.Ensures(value <= HorusLength());
                }
                int diff = value - this.Day;
                this = this.AddDays(diff);
            }
        }


        // Returns the hour part of this StarDate. The returned value is an
        // integer between 0 and 23.

        public int Hour
        {
            get
            {
                if (StarCulture.CurrentCulture.ThirtyHour)
                {
                    Contract.Ensures(Contract.Result<int>() >= 0);
                    Contract.Ensures(Contract.Result<int>() < 30);
                    int h = (int)(this.TimeOfDay.Ticks / TicksPerHour);
                    if (h < 6)
                    {
                        h += 24;
                    }
                    return h;
                }
                else
                {
                    Contract.Ensures(Contract.Result<int>() >= 0);
                    Contract.Ensures(Contract.Result<int>() < 24);
                    return (int)(TimeTicks / TicksPerHour);
                }
            }
            set
            {
                int h = value;
                int diff = h - this.Hour;
                this = AddHours(diff);
            }
        }


        // Returns the minute part of this StarDate. The returned value is
        // an integer between 0 and 59.
        //
        public int Minute
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 0);
                Contract.Ensures(Contract.Result<int>() < 60);
                return (int)((TimeTicks / TicksPerMinute) % 60);
            }
            set
            {
                int h = value;
                int diff = h - this.Minute;
                this = AddMinutes(diff);
            }
        }


        // Returns the second part of this StarDate. The returned value is
        // an integer between 0 and 59.
        //
        public int Second
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 0);
                Contract.Ensures(Contract.Result<int>() < 60);
                return (int)((TimeTicks / TicksPerSecond) % 60);
            }
            set
            {
                int diff = value - this.Second;
                this = AddSeconds(diff);
            }
        }


        // Returns the millisecond part of this StarDate. The returned value
        // is an integer between 0 and 999.
        //

        public int Millisecond
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 0);
                Contract.Ensures(Contract.Result<int>() < 1000);
                return (int)((TimeTicks / TicksPerMillisecond) % 1000);
            }
            set
            {
                int diff = value - this.Millisecond;
                this = AddMilliseconds(diff);
            }
        }


        // Returns Ticks of this stardate that are not in a full millisecond
        // integer between 1 and 10000.

        public int ExtraTicks
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 0);
                Contract.Ensures(Contract.Result<int>() < 10000);
                return (int)((TimeTicks % TicksPerMillisecond));
            }
            set
            {
                int diff = value - this.ExtraTicks;
                this.internalTicks += diff;
            }
        }




        // Returns the tick count for this StarDate. The returned value is
        // the number of 100-nanosecond intervals that have elapsed since the rounded date of the Big Bang 
        //
        public BigInteger Ticks
        {
            get
            {
                return internalTicks;
            }
            set
            {
                this.internalTicks = value;
            }
        }

        // Returns the time-of-day part of this StarDate. The returned value
        // is a TimeSpan that indicates the time elapsed since midnight.
        //
        public Time TimeOfDay
        {
            get
            {
                return new Time(AdjustedTicks % TicksPerDay);
            }
            internal set
            {
                Time diff = value - this.TimeOfDay;
                this.Atomic += diff;
            }
        }


        //returns the name of the month


        public string MonthName
        {
            get
            {
                return StarCulture.CurrentCulture.GetMonthName(Month);
            }
        }

        //returns the symbol of the month


        public string MonthSymbol
        {
            get
            {
                return StarCulture.MonthSymbols[Month];
            }
        }

        // Returns the day-of-week part of this StarDate. The returned value
        // is an integer between 0 and 6, where 0 indicates Sunday, 1 indicates
        // Monday, 2 indicates Tuesday, 3 indicates Wednesday, 4 indicates
        // Thursday, 5 indicates Friday, and 6 indicates Saturday.
        // Based on localization it prints as a day of the week
        //

        public DayOfWeek DayOfWeek
        {
            get
            {
                Contract.Ensures(Contract.Result<DayOfWeek>() >= DayOfWeek.Sunday);
                Contract.Ensures(Contract.Result<DayOfWeek>() <= DayOfWeek.Saturday);
                return (DayOfWeek)(GetDatePart(DatePartDayOfWeek));
            }
            set
            {
                int d = (int)value;
                if (d == 0) d = 7;
                int diff = d - (int)this.DayOfWeek;
                this.Atomic += diff * StarDate.DayTime;
            }
        }

        public string DayName
        {
            get
            {
                return StarCulture.CurrentCulture.DayNames[(int)DayOfWeek];
            }
        }

        //returns the symbol of the day

        public string DaySymbol
        {
            get
            {
                return StarCulture.DaySymbols[(int)DayOfWeek];
            }
        }

        public long Julian
        {
            get
            {
                return ((this - StarDate.julian) / StarDate.DayTime) + 1;
            }

            set
            {
                long diff = value - this.Julian;
                this += diff * StarDate.DayTime;
            }
        }

        //public bool HasYear { get => this.error < YearTime; }
        //public bool HasMonth { get => this.error < MonthTime; }
        //public bool HasDay { get => this.error < LocalDay; }
        //public bool HasHour { get => this.error < HourTime; }
        //public bool HasMinute { get => this.error < MinuteTime; }
        //public bool HasSecond { get => this.error < SecondTime; }
        //public bool HasMillisecond { get => this.error < MillisecondTime; }
        //public bool HasTick { get => this.accuracy == 0; }


        //returns Atomic Clock Time

        public Time Atomic
        {
            get
            {
                return new Time(internalTicks);
            }

            private set
            {
                internalTicks = value.Ticks;
            }
        }

        //returns Time of transmissions from Earth you are currently receiving (useful for movie releases and similar)

        public Time Radio
        {
            get
            {
                return this.TimeZone.ToRadio(this.Atomic);
            }

            internal set
            {
                this.Atomic = this.TimeZone.FromRadio(value);
            }
        }

        //returns time on Earth

        public Time Terra
        {
            get
            {
                return this.TimeZone.ToTerran(this.Atomic);
            }

            internal set
            {
                this.Atomic = this.TimeZone.FromTerran(value);
            }
        }

        //returns the time when your transmissions will arrive on Earth (useful for sending Merry Christmas messages to people on Earth)

        public Time Arrival
        {
            get
            {
                return this.TimeZone.ToArrival(this.Atomic);
            }

            internal set
            {
                this.Atomic = this.TimeZone.FromArrival(value);
            }
        }

        /// <summary>
        /// Static Properties
        /// </summary>


        // Returns a StarDate representing the current date and time. The
        // resolution of the returned value depends on the system timer. For
        // Windows NT 3.5 and later the timer resolution is approximately 10ms,
        // for Windows NT 3.1 it is approximately 16ms, and for Windows 95 and 98
        // it is approximately 55ms.

        public static StarDate Now
        {
            get { return new StarDate(DateTime.UtcNow, StarZone.Local); }
        }
        public static StarDate UtcNow
        {
            get
            {
                return new StarDate(DateTime.UtcNow, StarZone.UTC);
            }
        }

        public static StarZone Local
        {
            get
            {
                return StarZone.Local;
            }
        }


        public static StarZone UTC
        {
            get
            {
                return StarZone.UTC;
            }
        }

        public static BigInteger NetStart
        {
            get
            {
                return ADStart.Ticks;
            }
        }




        public static StarDate Manu
        {
            get
            {
                return StarDate.manu;
            }
        }
        public static StarDate MaxManu
        {
            get
            {
                return StarDate.maxManu;
            }
        }
        public static StarDate Maya { get => maya; internal set => maya1 = value; }

        public static StarDate MinValue
        {
            get
            {
                return (StarDate)DateTime.MinValue;
            }
        }

        public static StarDate MaxValue
        {
            get
            {
                return (StarDate)DateTime.MaxValue;
            }
        }

        public static StarZone UnspecifiedTimeZone
        {
            get
            {
                return StarZone.Unspecified;
            }
        }

        public static List<string> Formats
        {
            get
            {
                if (formats == null)
                {
                    formats = new List<string> { "yyyy-MM-dd" };
                }
                return formats;
            }

            private set
            {
                formats = value;
            }
        }

        public static int DaysInMonth(int year, int month)
        {
            Contract.Ensures(month >= 1 && month <= 14);
            if (month == 14)
            {
                return HorusLength(year);
            }
            else
            {
                return 28;
            }
        }

        public BigInteger TimeTicks { get => TimeOfDay.Ticks; }
        public Accuracy Accuracy { get => accuracy; set => accuracy = value; }
        public bool AgeOfManu
        {
            get
            {
                return this >= Manu && this <= MaxManu;
            }
        }

        public int Era
        {
            get
            {
                if (AgeOfManu)
                {
                    return StarDate.ManuInt;
                }
                else
                {
                    return GetEra(this);
                }
            }
        }

        private static int GetEra(StarDate dt)
        {
            int i = 0;
            while (true)
            {
                if (dt >= Eras[i] && dt <= Eras[i + 1])
                {
                    return i;
                }
                else
                {
                    i++;
                }
            }
        }

        public static StarDate[] Eras
        {
            get
            {
                if (eras == null)
                {
                    eras = new StarDate[]
                    {
                        new StarDate((BigInteger) 0),
                        new StarDate(b),
                        new StarDate(b * 2),
                        new StarDate(b * 3),
                        new StarDate(b * 4),
                        new StarDate(b * 5),
                        new StarDate(b * 6),
                        new StarDate(b * 7),
                        new StarDate(b * 8),
                        new StarDate(b * 9),
                        new StarDate(b * 10),
                        new StarDate(b * 11),
                        new StarDate(b * 12),
                        new StarDate(b * 13),
                        Manu,
                        MaxManu,
                        new StarDate(b * 15),
                        new StarDate(b * 16),
                        new StarDate(b * 17),
                        new StarDate(b * 18),
                        new StarDate(b * 19),
                        new StarDate(b * 20)
                    };
                }
                return eras;
            }
        }

        internal static bool TryToStarDate(int year, int month, int day, int hour, int minute, int second, int v, int era, out StarDate time)
        {
            throw new NotImplementedException();
        }

        public static int ManuInt
        {
            get
            {
                if (manuInt == -1)
                {
                    manuInt = GetEra(Maya);
                }
                return manuInt;
            }
        }

        public static long MinOffset { get; internal set; }
        public static long MaxOffset { get; internal set; }











        // Checks whether a given Year is a leap Year. This method returns true if
        // Year is a leap Year, or false if not.
        //
        public static bool IsGregLeapYear(int year)
        {
            if (year < 1)
            {
                year++;
            }
            return year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
        }

        public Time Subtract(StarDate value)
        {
            return new Time(AdjustedTicks - value.AdjustedTicks);
        }

        public Time Subtract(DateTime value)
        {
            return this.Subtract((StarDate)value);
        }

        public StarDate Subtract(TimeSpan value)
        {
            return Subtract(new Time(value));
        }

        public StarDate Subtract(Time value)
        {
            StarDate d = this;
            return d.AddTicks(value.Negate().Ticks);
        }

        // This function is duplicated in COMStarDate.cpp
        private static double TicksToOADate(long value)
        {
            if (value == 0)
                return 0.0;  // Returns OleAut's zero'ed date value.
            if (value < TicksPerDay) // This is a fix for VB. They want the default day to be 1/1/0001 rathar then 12/30/1899.
                value += DoubleDateOffset; // We could have moved this fix down but we would like to keep the bounds check.
            if (value < OADateMinAsTicks)
                throw new OverflowException(); //Environment.GetResourceString("Arg_OleAutDateInvalid"));
            // Currently, our max date == OA's max date (12/31/9999), so we don't
            // need an overflow check in that direction.
            long millis = (value - DoubleDateOffset) / TicksPerMillisecond;
            if (millis < 0)
            {
                long frac = millis % MillisPerDay;
                if (frac != 0) millis -= (MillisPerDay + frac) * 2;
            }
            return (double)millis / MillisPerDay;
        }

        // Converts the StarDate instance into an OLE Automation compatible
        // double date.
        public double ToOADate()
        {
            return TicksToOADate((long)(AdjustedTicks - NetStart));
        }

        public long ToFileTime()
        {
            // Treats the input as local if it is not specified
            return ToUniversalTime().ToFileTimeUtc();
        }

        public long ToFileTimeUtc()
        {
            // Treats the input as universal if it is not specified
            //BigInteger ticks = ((Kind & LocalMask) != 0) ? ToUniversalTime().TimeTicks : this.TimeTicks;
            return DateTime.ToFileTimeUtc();
        }

        public StarDate ToLocalTime()
        {
            return ToLocalTime(false);
        }

        internal StarDate ToLocalTime(bool throwOnOverflow)
        {
            return this.ToZone(Local);
        }

        public StarDate ToZone(StarZone zone)
        {
            StarDate dt = this;
            dt.TimeZone = zone;
            return dt;
        }

        public string ToLongString()
        {
            return ToLongDateString() + " " + ToLongTimeString();
        }

        public String ToLongDateString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            return StarDateFormat.Format(this, "D", StarCulture.CurrentCulture);
        }

        public String ToLongTimeString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            return StarDateFormat.Format(this, "T", StarCulture.CurrentCulture);
        }

        public string ToShortString()
        {
            return ToShortDateString() + " " + ToShortTimeString();
        }

        public String ToShortDateString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            return StarDateFormat.Format(this, "d", StarCulture.CurrentCulture);
        }

        public String ToShortTimeString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            return StarDateFormat.Format(this, "t", StarCulture.CurrentCulture);
        }

        public StarDate ToUniversalTime()
        {
            return this.ToZone(UTC);
        }


        /// <internalonly/>
        long IConvertible.ToInt64(IFormatProvider provider)
        {
            return DateTime.ToBinary();
        }

        /// <internalonly/>
        double IConvertible.ToDouble(IFormatProvider provider)
        {
            return ToOADate();
        }


        public int CompareTo(DateTime other) //[AllowNull]
        {
            return CompareTo((StarDate)other);
        }

        public bool Equals(DateTime other) //[AllowNull]
        {
            if (other == null)
            {
                return false;
            }
            else
            {
                return this.Equals((StarDate)other);
            }
        }




        DateTime IConvertible.ToDateTime(IFormatProvider provider)
        {
            return DateTime;
        }

        string IConvertible.ToString(IFormatProvider provider)
        {
            return ToString();
        }

        /// <summary>
        /// Parsing
        /// </summary>
        /// 

        // Constructs a StarDate from a string. The string must specify a
        // date and optionally a time in a culture-specific or universal format.
        // Leading and trailing whitespace characters are allowed.
        //
        public static StarDate Parse(String s)
        {
            StarDate sd;
            if (StarDate.TryDataParse(s, out sd))
            {
                return sd;
            }
            return (StarDateParse.Parse(s, StarCulture.CurrentCulture, StarDateStyles.None));
        }

        // Constructs a StarDate from a string. The string must specify a
        // date and optionally a time in a culture-specific or universal format.
        // Leading and trailing whitespace characters are allowed.
        //
        public static StarDate Parse(String s, IFormatProvider provider)
        {
            return (StarDateParse.Parse(s, StarCulture.GetInstance(provider), StarDateStyles.None));
        }

        public static StarDate Parse(String s, IFormatProvider provider, StarDateStyles styles)
        {
            StarCulture.ValidateStyles(styles, "styles");
            return (StarDateParse.Parse(s, StarCulture.GetInstance(provider), styles));
        }

        // Constructs a StarDate from a string. The string must specify a
        // date and optionally a time in a culture-specific or universal format.
        // Leading and trailing whitespace characters are allowed.
        //
        public static StarDate ParseExact(String s, String format)
        {
            return StarDateParse.ParseExact(s, format);
        }

        // Constructs a StarDate from a string. The string must specify a
        // date and optionally a time in a culture-specific or universal format.
        // Leading and trailing whitespace characters are allowed.
        //
        public static StarDate ParseExact(String s, String format, IFormatProvider provider)
        {
            return (StarDateParse.ParseExact(s, format, StarCulture.GetInstance(provider), StarDateStyles.None));
        }

        // Constructs a StarDate from a string. The string must specify a
        // date and optionally a time in a culture-specific or universal format.
        // Leading and trailing whitespace characters are allowed.
        //
        public static StarDate ParseExact(String s, String format, IFormatProvider provider, StarDateStyles style)
        {
            StarCulture.ValidateStyles(style, "style");
            return (StarDateParse.ParseExact(s, format, StarCulture.GetInstance(provider), style));
        }

        public static StarDate ParseExact(String s, String[] formats, IFormatProvider provider, StarDateStyles style)
        {
            StarCulture.ValidateStyles(style, "style");
            return StarDateParse.ParseExactMultiple(s, formats, StarCulture.GetInstance(provider), style);
        }

        public static Boolean TryParse(String s, out StarDate result)
        {
            return StarDateParse.TryParse(s, StarCulture.CurrentCulture, StarDateStyles.None, out result);
        }

        public static Boolean TryParse(String s, IFormatProvider provider, StarDateStyles styles, out StarDate result)
        {
            StarCulture.ValidateStyles(styles, "styles");
            return StarDateParse.TryParse(s, StarCulture.GetInstance(provider), styles, out result);
        }

        public static Boolean TryParseExact(String s, String format, IFormatProvider provider, StarDateStyles style, out StarDate result)
        {
            StarCulture.ValidateStyles(style, "style");
            return StarDateParse.TryParseExact(s, format, StarCulture.GetInstance(provider), style, out result);
        }

        public static Boolean TryParseExact(String s, String[] formats, IFormatProvider provider, StarDateStyles style, out StarDate result)
        {
            StarCulture.ValidateStyles(style, "style");
            return StarDateParse.TryParseExactMultiple(s, formats, StarCulture.GetInstance(provider), style, out result);
        }

        /// <summary>
        /// Operators
        /// </summary>


        public static StarDate operator +(StarDate d, Time t)
        {
            StarDate dt = d;
            dt.Atomic += t;
            return dt;
        }

        public static StarDate operator -(StarDate d, Time t)
        {
            StarDate dt = d;
            dt.Atomic -= t;
            return dt;
        }

        public static StarDate operator +(StarDate d, TimeSpan t)
        {
            return d.Add(t);
        }

        public static StarDate operator -(StarDate d, TimeSpan t)
        {
            return d.Subtract(t);
        }

        public static StarDate operator +(StarDate d, BigInteger t)
        {
            return d.AddTicks(t);
        }

        public static StarDate operator -(StarDate d, BigInteger t)
        {
            return d.AddTicks(-1 * t);
        }

        public static Time operator -(StarDate d1, StarDate d2)
        {
            return d1.Subtract(d2);
        }

        public static bool operator ==(StarDate dt1, StarDate dt2)
        {
            return dt1.Equals(dt2);
        }

        public static bool operator !=(StarDate dt1, StarDate dt2)
        {
            return !dt1.Equals(dt2);
        }

        public static bool operator <(StarDate dt1, StarDate dt2)
        {
            return dt1.Atomic < dt2.Atomic;
        }

        public static bool operator >(StarDate dt1, StarDate dt2)
        {
            return dt1.Atomic > dt2.Atomic;
        }


        public static bool operator <=(StarDate dt1, StarDate dt2)
        {
            if (dt1 < dt2)
            {
                return true;
            }
            else if (dt1 == dt2)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static bool operator >=(StarDate dt1, StarDate dt2)
        {
            if (dt1 > dt2)
            {
                return true;
            }
            else if (dt1 == dt2)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static StarDate operator ++(StarDate dt)
        {
            return dt + DayTime;
        }

        public static StarDate operator --(StarDate dt)
        {
            return dt - DayTime;
        }

        public static explicit operator StarDate(string s)
        {
            return DataParse(s);
        }


        public static implicit operator DateTime(StarDate dt)
        {
            return dt.DateTime;
        }


        public static implicit operator StarDate(DateTime v)
        {
            return new StarDate(v);
        }


        public string ToString(string format, IFormatProvider formatProvider)
        {
            if (format == null)
            {
                return ToString();
            }
            return ToString(format);
        }

        public int GetMonthDays()
        {
            if (Month == 14)
            {
                return HorusLength();
            }
            else
            {
                return 28;
            }
        }

        public int GetYearMonths()
        {
            if (isleapyear())
            {
                return 14;
            }
            else
            {
                return 13;
            }
        }

        public string Data
        {
            get
            {
                long[] values;
                GetDatePart(out values);
                int i = 0;
                StringBuilder builder = new StringBuilder();
                while (i < (int)Accuracy)
                {
                    builder.Append(values[i++] + "-");
                }
                //builder.Append(accuracy + "-");
                builder.Append(TimeZone.Id);
                return builder.ToString();
            }
            set
            {
                StarDate sd;
                if (TryDataParse(value, out sd))
                {
                    internalTicks = sd.internalTicks;
                    accuracy = sd.accuracy;
                    _timeZone = sd.TimeZone;
                }
            }
        }

        public static StarCulture CurrentCulture { get => StarCulture.CurrentCulture; private set => StarCulture.CurrentCulture = value; }

        //"yyyyy/MM/dd hh:mm:ss tt zzzz"

        public static bool TryDataParse(string text, out StarDate converted)
        {
            string[] data = text.Split('-');
            StarZone timeZone = UTC;
            try
            {
                timeZone = StarZone.FindSystemTimeZoneById(data[data.Length - 1]);
                string[] vs = new string[data.Length - 1];
                int i = 0;
                while (i < vs.Length)
                {
                    vs[i] = data[i];
                    i++;
                }
                data = vs;
            }
            catch (KeyNotFoundException)
            {
                //timeZone = UTC;
            }
            try
            {
                switch (data.Length)
                {
                    case 1:
                        converted = new StarDate(long.Parse(data[0]), timeZone);
                        return true;
                    case 2:
                        converted = new StarDate(long.Parse(data[0]), long.Parse(data[1]), timeZone);
                        return true;
                    case 3:
                        converted = new StarDate(long.Parse(data[0]), long.Parse(data[1]), long.Parse(data[2]), timeZone);
                        return true;
                    case 4:
                        converted = new StarDate(long.Parse(data[0]), long.Parse(data[1]), long.Parse(data[2]), long.Parse(data[3]), timeZone);
                        return true;
                    case 5:
                        converted = new StarDate(long.Parse(data[0]), long.Parse(data[1]), long.Parse(data[2]), long.Parse(data[3]), long.Parse(data[4]), timeZone);
                        return true;
                    case 6:
                        converted = new StarDate(long.Parse(data[0]), long.Parse(data[1]), long.Parse(data[2]), long.Parse(data[3]), long.Parse(data[4]), long.Parse(data[5]), timeZone);
                        return true;
                    case 7:
                        converted = new StarDate(long.Parse(data[0]), long.Parse(data[1]), long.Parse(data[2]), long.Parse(data[3]), long.Parse(data[4]), long.Parse(data[5]), long.Parse(data[6]), timeZone);
                        return true;
                    case 8:
                    default:
                        converted = new StarDate(long.Parse(data[0]), long.Parse(data[1]), long.Parse(data[2]), long.Parse(data[3]), long.Parse(data[4]), long.Parse(data[5]), long.Parse(data[6]), long.Parse(data[7]), timeZone);
                        return true;
                }
            }
            catch (ArgumentOutOfRangeException)
            {
                converted = default;
                return false;
            }
            catch (FormatException)
            {
                converted = default;
                return false;
            }
        }

        public static StarDate DataParse(string basic)
        {
            StarDate dt;
            TryDataParse(basic, out dt);
            return dt;
        }

        internal static bool EnableAmPmParseAdjustment()
        {
            throw new NotImplementedException();
        }

        public XmlSchema GetSchema() { return null; }

        public void ReadXml(XmlReader reader)
        {
            Data = reader["Data"];
        }

        public void WriteXml(XmlWriter writer)
        {
            writer.WriteAttributeString("Data", Data);
        }

        public TypeCode GetTypeCode()
        {
            return ((IConvertible)Data).GetTypeCode();
        }

        public bool ToBoolean(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToBoolean(provider);
        }

        public byte ToByte(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToByte(provider);
        }

        public char ToChar(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToChar(provider);
        }

        public decimal ToDecimal(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToDecimal(provider);
        }

        public short ToInt16(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToInt16(provider);
        }

        public int ToInt32(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToInt32(provider);
        }

        public sbyte ToSByte(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToSByte(provider);
        }

        public float ToSingle(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToSingle(provider);
        }

        public object ToType(Type conversionType, IFormatProvider provider)
        {
            return ((IConvertible)Data).ToType(conversionType, provider);
        }

        public ushort ToUInt16(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToUInt16(provider);
        }

        public uint ToUInt32(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToUInt32(provider);
        }

        public ulong ToUInt64(IFormatProvider provider)
        {
            return ((IConvertible)Data).ToUInt64(provider);
        }

        public void TestYear()
        {
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            //if (IsTerran == false)
            //{
            //    throw new NotImplementedException();
            //}
            int y100k = (int)(n / DaysPer100k);
            //if (part == DatePart100k) return 100 * k * y100k;
            Console.WriteLine(100 * k + y100k);
            n -= y100k * DaysPer100k;
            int y78 = (int)(n / DaysPer78Years);
            n -= y78 * DaysPer78Years;
            int y6 = (int)(n / DaysPerSixYears);
            if (y6 == 13) y6 = 12;
            n -= y6 * DaysPerSixYears;
            int y1 = (int)(n / DaysPerYear);
            if (y1 == 6) y1 = 5;
            //if (part == DatePartYear) return 100 * k * (long) y100k + 78 * (long) y78 + 6 * (long)y6 + (long)y1;
            Console.WriteLine("DatePartYear " + 100 * k * (long)y100k + 78 * (long)y78 + 6 * (long)y6 + (long)y1);
            n -= y1 * DaysPerYear;
            int d = (int)n + 1;
            //if (part == DatePartDayOfYear) return d;
            Console.WriteLine(d);
            //if (part == DatePartMonth) return ((d - 1) / 28) + 1;
            Console.WriteLine(((d - 1) / 28) + 1);
            d %= 28;
            if (d == 0) d = 28;
            //if (part == DatePartDay) return d;
            Console.WriteLine(d);
            //else if (part == DatePartDayOfWeek) return d % 7;
            Console.WriteLine(d % 7);
            //else
            //{
            //    return 19;
            //}
        }

        public string Stored()
        {
            throw new NotImplementedException();
        }

        public string TestToStringAndParse()
        {
            return TestToStringAndParse(DefaultFormat);
        }

        public static string DefaultFormat
        {
            get
            {
                return defaultFormat();
            }
        }

        private static string defaultFormat()
        {
            return defaultFormat(CurrentCulture);
        }

        private static string defaultFormat(StarCulture local)
        {
            if (StarDate.LongDefault)
            {
                return local.FullStarDatePattern;
            }
            else
            {
                return local.ShortStarDatePattern;
            }
        }

        public string TestToStringAndParse(string format)
        {
            string s = ToString(format);
            Console.WriteLine("Input: " + s);
            this = ParseExact(s, format);
            return ToString(format);
        }

        public static void WriteIcal(string v)
        {
            WriteIcal(v, DateTime.Now.Year);
        }

        public static void WriteIcal(string v1, int v2)
        {
            WriteIcal(v1, v2, v2);
        }

        public static void WriteIcal(string path, int v2, int v3)
        {
            string[] p = path.Split('/');
            string filename = p[p.Length - 1];
            int i = 0;
            StringBuilder stringBuilder = new StringBuilder();
            while (i < p.Length - 1)
            {
                stringBuilder.Append(p[i]);
                stringBuilder.Append('/');
            }
            path = stringBuilder.ToString();
            if (filename.Length == 0)
            {
                if (v2 == v3)
                {
                    filename = "StarCalendar_of_" + v2 + ".ics";
                }
                else
                {
                    filename = "StarCalendar_of_" + v2 + "_to_" + v3 + ".ics";
                }
            }
            else if (!filename.EndsWith(".ics"))
            {
                filename += ".ics";
            }

            //Path filepath = $"{path}{filename}";

            //StreamWriter ical = new StreamWriter(path + filename);
        }

        public string RFC1123
        {
            get
            {
                return DateTimeUTC.ToString("R");
            }
        }
    }
}