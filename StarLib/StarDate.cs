using System;
using System.Collections.Generic;
using System.Diagnostics.Contracts;
using System.Globalization;
using System.IO;
using System.Management.Automation;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;

namespace StarLib
{



    // This value type represents a date and time.  Every StarDate
    // object has a private field (Ticks) of type Int64 that stores the
    // date and time as the number of 100 nanosecond intervals since
    // 12:00 AM January 1, Year 1 A.D. in the proleptic Gregorian Calendar.
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
(G)     "s"                 Sortable format, based on ISO 8601.     "yyyy-MM-dd'T'HH:mm:ss"                 11999-10-28T02:00:00
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
    [Serializable]
    public struct StarDate : IComparable<StarDate>, IEquatable<StarDate>, IComparable, IFormattable, IConvertible, ISerializable, IComparable<DateTime>, IEquatable<DateTime>
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
        internal static Time DayTime = HourTime * 24;
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
        internal static Time month = week * 4;
        internal const long TicksPerMonth = TicksPerDay * 28;
        internal const int DaysPerMonth = DaysPerWeek * 4;
        internal static Time YearTime = week * 52;
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
        //internal static Time SiderealYear = Day * 365.25636;
        internal static Time SiderealYear = Seventy_Eight / 78;
        internal static Time k = SiderealYear * 1000;
        internal static BigInteger TicksPerThousand = TicksPerAverageYear * 1000;
        internal const long DaysPerThousand = DaysPerAverageYear * 1000;
        internal static Time m = k * 1000;
        internal static BigInteger TicksPerMillion = TicksPerThousand * 1000;
        internal const long DaysPerMillion = DaysPerThousand * 1000;
        internal static Time b = m * 1000;
        internal static BigInteger TicksPerBillion = TicksPerMillion * 1000;
        internal const long DaysPerBillion = DaysPerMillion * 1000;
        internal const long DaysPerTrillion = DaysPerBillion * 1000;
        internal const long DaysPerQuadrillion = DaysPerTrillion * 1000;
        internal static Time a = 200 * m;
        private static readonly StarDate manu = StarDate.AbstractDate(((BigInteger)DaysPerBillion * TicksPerDay), 0, UTC);
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

        private const int DatePartQuadrillion = -4;
        private const int DatePartTrillion = -3;
        private const int DatePartBillion = -2;
        private const int DatePartMillion = -1;
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
        private const String DateDataField = "dateData";

        // The data is stored as an unsigned 64-bit integer
        //   Bits 01-62: The value of 100-nanosecond _ticks where 0 represents 1/1/0001 12:00am, up until the value
        //               12/31/9999 23:59:59.PlaceHolder
        //   Bits 63-64: A four-state value that describes the DateTimeKind value of the date time, with a 2nd
        //               value for the rare case where the date time is local, but is in an overlapped daylight
        //               savings time hour and it is in daylight savings time. This allows distinction of these
        //               otherwise ambiguous local times and prevents data loss when round tripping from Local to
        //               UTC time.
        private BigInteger dateData;
        private BigInteger errorData;
        private StarZone _timeZone;
        private static IEnumerable<string> allFormats;
        private static IEnumerable<StarDate> testYear;
        private static string defaultFormat = "yyyyy/MM/dd hh:mm:ss tt zzzz";
        private static StarDate maya1;
        public static bool LongDefault = false; //switches whether the default tostring method prints a long date or a short date
        private static string currentCulture;
        private static List<string> formats;



        //private StarZone timezone;

        public StarDate TickTimeZoneConvert(StarZone z) //converts a timezone by treating the utc ticks in a StarDate as though they were the ticks of that timezone
        {
            return new StarDate(Year, Month, Day, Hour, Minute, Second, Millisecond);
        }



        public static StarDate StarHanukkah() //gives the date of hannukkah for this year
        {
            return new StarDate(GregHanukkah());
        }

        public static void MakeChart()
        {
            MakeChart("");
        }

        public static void MakeChart(int gregyear)
        {
            MakeChart("", gregyear);
        }

        public static void MakeChart(string v) //makes a chart for a year at the designated path
        {
            StarDate.MakeChart(v, DateTime.Now.Year);
        }

        public static void MakeChart(string path, int gregyear) //makes a chart for a year at the designated path
        {
            StreamWriter chart = new StreamWriter(path + "CosmicCalendar.csv");
            StarDate mi = StarDate.FromGreg(gregyear, 6, 2);
            int y = mi.Year;
            StarDate[] starDates = new StarDate[] { StarDate.FromGreg(gregyear, 1, 1), StarDate.FromGreg(gregyear, 12, 31), new StarDate(y, 1, 1), new StarDate(y + 1, 1, 1).AddDays(-1) };
            Array.Sort(starDates);
            StarDate dt = starDates[0];
            StarDate end = starDates[3];
            chart.WriteLine("short stardate, long stardate, Star Year, Star Month, Star Month Name, Month Symbol, Day of Star Year, Day of Star Month, Weekday, Weekday Symbol, short gregdate, long gregdate, gregyear, gegmonth, gregmonth name, greg day of year, greg day of month");
            while (dt <= end)
            {
                string data = "";
                data += dt.ToShortDateString(); data += ",";
                data += dt.ToLongDateString(); data += ",";
                data += dt.Year; data += ",";
                data += dt.Month; data += ",";
                data += dt.MonthName; data += ",";
                data += dt.MonthSymbol; data += ",";
                data += dt.DayOfYear; data += ",";
                data += dt.Day; data += ",";
                data += dt.DayOfWeek; data += ",";
                data += dt.DaySymbol; data += ",";
                data += dt.DateTime.ToShortDateString(); data += ",";
                data += dt.DateTime.ToLongDateString(); data += ",";
                data += dt.DateTime.Year; data += ",";
                data += dt.DateTime.Month; data += ",";
                data += dt.DateTime.ToString("MMMMMMMMM");
                data += dt.DateTime.DayOfYear; data += ",";
                data += dt.DateTime.Day; data += ",";
                chart.WriteLine(data);
                dt++;
            }
            chart.Flush();
            chart.Close();
            //throw new NotImplementedException();
        }

        internal static StarDate AbstractDate(Time timeSpanInfo)
        {
            StarDate dt = new StarDate(timeSpanInfo);

            dt.TimeZone = StarZone.Local;
            //dt.arraylength = 10;
            dt.errorData = 0;
            return dt;
        }



        public static StarDate StarHanukkah(DateTime dt) //
        {
            return new StarDate(GregHanukkah(dt));
        }

        public static StarDate StarHanukkah(StarDate dt)//
        {
            return new StarDate(GregHanukkah(dt));
        }

        public static DateTime GregHanukkah()//
        {
            return GregHanukkah(DateTime.Now);
        }

        public static DateTime GregHanukkah(DateTime now)//
        {
            System.Globalization.Calendar HebCal = new HebrewCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 11, 1);
            int hebyear = HebCal.GetYear(now);
            DateTime Hanukkah = new DateTime(hebyear, 3, 25, new HebrewCalendar());
            return Hanukkah;
        }


        public static DateTime GregHanukkah(StarDate dt)//
        {
            DateTime o = new StarDate(dt.Year, 12, 1).DateTime;
            return GregHanukkah(o);
        }





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
                    //throw new NotImplementedException();
                }
                else if (modifier == "BET")
                {
                    try
                    {
                        StarDate dt1 = StarDate.GregParse(parsedinput[1] + " " + parsedinput[2] + " " + parsedinput[3]);
                        StarDate dt2 = StarDate.GregParse(parsedinput[5] + " " + parsedinput[6] + " " + parsedinput[7]);
                        return Between(dt1, dt2);
                    }
                    catch (IndexOutOfRangeException)
                    {
                        return Between(StarDate.FromGreg(int.Parse(parsedinput[1])), StarDate.FromGreg(int.Parse(parsedinput[3])));
                    }
                }
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
                                    if ((parsedinput[1] == "AND"))
                                    {
                                        StarDate a = StarDate.FromGreg(int.Parse(parsedinput[0]));
                                        StarDate b = StarDate.FromGreg(int.Parse(parsedinput[2]));
                                        return Between(a, b);
                                    }
                                }
                            }

                        }
                    }
                    //throw new NotImplementedException();
                    //StarDate date = new StarDate(dt);
                    //date.addModifier(modifier);
                    return new StarDate((BigInteger)0);
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
            //throw new NotImplementedException();
        }




        private void adderror(Time error)
        {
            this.error = error;
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
                return this.ToLongDateString() + " " + this.ToLongTimeString();
            }
            else
            {
                return this.ToShortDateString() + " " + ToShortTimeString();
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
        private int GetDatePart(int part)
        {
            if (IsTerran == false)
            {
                throw new NotImplementedException();
            }
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            if (part == DatePartQuadrillion)
            {
                return (int)(n / DaysPerQuadrillion);
            }
            else if (part == DatePartTrillion)
            {
                return (int)((n % DaysPerQuadrillion) / DaysPerTrillion);
            }
            else if (part == DatePartBillion)
            {
                return (int)((n % DaysPerTrillion) / DaysPerBillion);
            }
            else if (part == DatePartMillion)
            {
                return (int)((n % DaysPerBillion) / DaysPerMillion);
            }
            else
            {
                n %= DaysPerBillion;
                n %= DaysPerMillion;
                //////////Console.WriteLine("Days Since Manu = " + n);
                //Logic Error is here
                //////////Console.WriteLine(DaysPerAverageYear);
                //////////Console.WriteLine(n / DaysPerAverageYear);
                ////////////Console.WriteLine()
                //throw new NotImplementedException();
                int y78 = (int)(n / DaysPer78Years);
                n -= y78 * DaysPer78Years;
                int y6 = (int)(n / DaysPerSixYears);
                if (y6 == 13) y6 = 12;
                n -= y6 * DaysPerSixYears;
                int y1 = (int)(n / DaysPerYear);
                if (y1 == 6) y1 = 5;
                if (part == DatePartYear) return 78 * y78 + 6 * y6 + y1;
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
        }

        // Exactly the same as GetDatePart(int part), except computing all of
        // Year/month/day rather than just one of them.  Used when all three
        // are needed rather than redoing the computations for each.
        internal void GetDatePart(out int year, out int month, out int day)
        {
            Int64 n = (long)(AdjustedTicks / TicksPerDay);
            if (IsTerran)
            {
                n %= DaysPerBillion;
                n %= DaysPerMillion;
                int y78 = (int)(n / DaysPer78Years);
                n -= y78 * DaysPer78Years;
                int y6 = (int)(n / DaysPerSixYears);
                if (y6 == 13) y6 = 12;
                n -= y6 * DaysPerSixYears;
                int y1 = (int)(n / DaysPerYear);
                if (y1 == 6) y1 = 5;
                year = 78 * y78 + 6 * y6 + y1;
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
                    //throw new NotImplementedException();
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
        //    throw new NotImplementedException();
        //}

        //private bool Sol => this.TimeZone.Sol;

        internal StarDate addtimezone(string prim)
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
            return isleapyear(Year) > 0;
        }

        public bool isDoubleLeapYear()
        {
            return isleapyear(Year) == 2;
        }


        public static int isleapyear(long year)
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
            //throw new NotImplementedException();
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


        public static DateTime GregChineseNewYear(DateTime now)
        {
            System.Globalization.Calendar Chinese = new ChineseLunisolarCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 4, 1);
            int ChinaYear = Chinese.GetYear(now);
            DateTime Hanukkah = new DateTime(ChinaYear, 1, 1, new ChineseLunisolarCalendar());
            return Hanukkah;
        }

        public static DateTime GregChineseNewYear()
        {
            return GregChineseNewYear(DateTime.Now);
        }


        public static StarDate StarPurim()
        {
            return new StarDate(GregPurim());
        }

        public static StarDate StarPurim(DateTime dt)
        {
            return new StarDate(GregPurim(dt));
        }

        public static StarDate StarPurim(StarDate dt)
        {
            return new StarDate(GregPurim(dt));
        }

        public static DateTime GregPurim()
        {
            return GregPurim(DateTime.Now);
        }

        public static DateTime GregPurim(DateTime now)
        {
            System.Globalization.Calendar HebCal = new HebrewCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 11, 1);
            int hebyear = HebCal.GetYear(now);
            DateTime Purim = new DateTime(hebyear, 6, 14, new HebrewCalendar());
            return Purim;
        }

        public static DateTime GregPurim(StarDate dt)
        {
            DateTime o = new StarDate(dt.Year, 12, 1).DateTime;
            return GregPurim(o);
        }

        // Constructs a StarDate from a tick count. The _ticks
        // argument specifies the date as the number of 100-nanosecond intervals
        // that have elapsed since 1/1/0001 12:00am.
        //
        public StarDate(BigInteger ticks)
        {
            dateData = (UInt64)ticks;
            _timeZone = StarZone.Local;
            errorData = 0;
        }


        public StarDate(BigInteger ticks, DateTimeKind kind) : this(ticks)
        {
            StarDate.SpecifyKind(this, kind);
        }

        public StarDate(BigInteger ticks, DateTimeKind kind, Boolean isAmbiguousDst)
        {
            this.dateData = ticks;
            this.errorData = 0;
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

        // Constructs a StarDate from a given Year, month, and day. The
        // time-of-day of the resulting StarDate is always midnight.
        //

        public StarDate(int year) : this(year, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(int year, StarZone zone) : this(year, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, zone)
        {

        }


        public StarDate(int year, int month) : this(year, month, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(int year, int month, StarZone zone) : this(year, month, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, zone)
        {

        }

        public StarDate(int year, int month, int day) : this(year, month, day, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(int year, int month, int day, StarZone timezone) : this(year, month, day, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, timezone)
        {

        }

        public StarDate(int year, int month, int day, int hour) : this(year, month, day, hour, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(int year, int month, int day, int hour, StarZone timezone) : this(year, month, day, hour, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, timezone)
        {

        }

        public StarDate(int year, int month, int day, int hour, int minute) : this(year, month, day, hour, minute, PlaceHolder, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(int year, int month, int day, int hour, int minute, StarZone timezone) : this(year, month, day, hour, minute, PlaceHolder, PlaceHolder, PlaceHolder, timezone)
        {

        }


        public StarDate(int year, int month, int day, int hour, int minute, int second) : this(year, month, day, hour, minute, second, PlaceHolder, PlaceHolder, Local)
        {

        }

        public StarDate(int year, int month, int day, int hour, int minute, int second, StarZone timezone) : this(year, month, day, hour, minute, second, PlaceHolder, PlaceHolder, timezone)
        {

        }


        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond) : this(year, month, day, hour, minute, second, millisecond, PlaceHolder, Local)
        {

        }

        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, StarZone timezone) : this(year, month, day, hour, minute, second, millisecond, PlaceHolder, timezone)
        {

        }

        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks) : this(year, month, day, hour, minute, second, millisecond, ticks, Local)
        {

        }

        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks, StarZone timezone)
        {
            //base constructor used to generate all dates from standard digits
            _timeZone = timezone;
            dateData = Manu.Ticks;
            int y78 = year / 78;
            year -= y78 * 78;
            int y6 = year / 6;
            year -= y6 * 6;
            dateData += y78 * TicksPerSeventyEightYears;
            dateData += y6 * TicksPerSixYears;
            dateData += year * TicksPerYear;
            if (!isvalidhorus(year, month, day))
            {
                throw new Exception("Invalid Leap Year");
            }
            else if (month == PlaceHolder)
            {
                switch (LeapType(year))
                {
                    case 0:
                        errorData = 26 * TicksPerWeek;
                        break;
                    case 1:
                        errorData = 26 * TicksPerWeek + 3 * TicksPerDay + 12 * TicksPerHour;
                        break;
                    default:
                        errorData = 27 * TicksPerWeek;
                        break;
                }
                dateData += errorData;
            }
            else if (month < 1 || month > 14)
            {
                throw new ArgumentOutOfRangeException("Month");
            }
            else
            {
                dateData += (month - 1) * TicksPerMonth;
                if (day == PlaceHolder)
                {
                    if (month == 14)
                    {
                        switch (LeapType(year))
                        {
                            case 0:
                                throw new Exception("Invalid Leap Year");
                            case 1:
                                errorData = 3 * TicksPerDay + 12 * TicksPerHour;
                                break;
                            default:
                                errorData = TicksPerWeek;
                                break;
                        }
                    }
                    else
                    {
                        errorData = 14 * TicksPerDay;
                    }
                    dateData += errorData;
                }
                else if (day < 1 || day > 28)
                {
                    throw new ArgumentOutOfRangeException("Day");
                }
                else
                {
                    dateData += TicksPerDay;
                    //adjusting for timezone
                    //subtract datetime offset because internal ticks refer to UTC Atomic time
                    if (_timeZone.SupportsDaylightSavingTime)
                    {
                        dateData -= _timeZone.GetUtcOffset(dateData);
                    }
                    else
                    {
                        dateData += _timeZone.BaseUtcOffset.Ticks;
                    }
                    if (hour == PlaceHolder)
                    {
                        errorData = 12 * TicksPerHour;
                        dateData += errorData;
                    }
                    else if (hour < 0 || hour > 30)
                    {
                        throw new ArgumentOutOfRangeException("Hour");
                    }
                    else
                    {
                        dateData += hour * TicksPerHour;
                        if (minute == PlaceHolder)
                        {
                            errorData = 30 * TicksPerMinute;
                            dateData += errorData;
                        }
                        else if (minute < 0 || minute > 59)
                        {
                            throw new ArgumentOutOfRangeException("Minute");
                        }
                        else
                        {

                            if (second == PlaceHolder)
                            {
                                errorData = 30 * TicksPerSecond;
                                dateData += errorData;
                            }
                            else if (second < 0 || second > 60)
                            {
                                throw new ArgumentOutOfRangeException("second");
                            }
                            else
                            {
                                if (second == 60)
                                {
                                    if (StarDate.LeapSeconds(dateData, year, month, day, hour, minute, second, DateTimeKind.Unspecified))
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
                                dateData += second * TicksPerSecond;
                                if (millisecond == PlaceHolder)
                                {
                                    errorData = 500 * TicksPerMillisecond;
                                    dateData += errorData;
                                }
                                else if (millisecond < 0 || millisecond > 1000)
                                {
                                    throw new ArgumentOutOfRangeException("millisecond");
                                }
                                else
                                {

                                    if (ticks == PlaceHolder)
                                    {
                                        errorData = 5000 * TicksPerMillisecond;
                                        dateData += errorData;
                                    }
                                    else if (ticks < 0 || ticks > 10000)
                                    {
                                        throw new ArgumentOutOfRangeException("ticks");
                                    }
                                    else
                                    {
                                        dateData += ticks;
                                        errorData = 0;
                                    }
                                }

                            }

                        }

                    }

                }
            }
        }

        private static bool LeapSeconds(BigInteger dateData, int year, int month, int day, int hour, int minute, int second, DateTimeKind unspecified)
        {
            DateTime dt = new DateTime((long)(dateData - Manu.Ticks)).Date;
            year = dt.Year;
            month = dt.Month;
            day = dt.Day;
            try
            {
                DateTime test = new DateTime(year, month, day, hour, minute, second);
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }

        private static bool isvalidhorus(int year, int month, int day)
        {
            if (month == 14)
            {
                int v = isleapyear(year);
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

        private static int LeapType(int year)
        {
            throw new NotImplementedException();
        }

        internal static StarDate fromdigits(StarZone z, int year, int month, int day, int hour, int min, int second, int millisecond, int ticks)
        {
            StarDate dt = Manu;
            int y78 = year / 78;
            year -= y78 * 78;
            int y6 = year / 6;
            year -= y6 * 6;
            dt += y78 * Seventy_Eight;
            dt += y6 * Sixyear;
            dt += year * YearTime;
            dt += month * StarDate.month;
            dt += day * StarDate.DayTime;
            dt += hour * StarDate.HourTime;
            dt += min * StarDate.MinuteTime;
            dt += second * StarDate.SecondTime;
            dt += millisecond * StarDate.MillisecondTime;
            dt += new Time(ticks);
            dt -= z.Offset(dt);
            //throw new NotImplementedException();
            return dt;
        }

        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks, Time error) : this(year, month, day, hour, minute, second, millisecond, ticks, Local)
        {
            this.errorData = error;
        }

        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks, Time error, StarZone uTC) : this(year, month, day, hour, minute, second, millisecond, ticks, uTC)
        {
            this.errorData = error;
        }

        public StarDate(BigInteger ticks, BigInteger error, StarZone zone)
        {
            dateData = ticks;
            errorData = error;
            _timeZone = zone;
        }

        public StarDate(BigInteger ticks, BigInteger errorData, DateTimeKind kind) : this(ticks, errorData, StarZone.FromKind(kind))
        {

        }

        public StarDate(DateTime dt)
        {
            dateData = NetStart + dt.Ticks;
            errorData = 0;
            if (dt.Kind == DateTimeKind.Local)
            {
                this._timeZone = Local;
                dateData -= Local.Offset(dt).Ticks;
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

        public StarDate(Time t) : this()
        {
            this.Atomic = t;
            this.TimeZone = StarZone.Local;
        }

        public StarDate(BigInteger v, StarZone Zone) : this(v)
        {
            this.Atomic = new Time(v) + ADStart.Atomic;
            this.TimeZone = Zone;
        }



        public StarDate(DateTime utcNow, StarZone zone) : this(utcNow)
        {
            this.TimeZone = zone;
        }


        public StarDate(Time t, StarZone zone) : this(t)
        {
            this.Atomic = t;
            this.TimeZone = zone;
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
            return this + new Time(ticks);
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
        public StarDate AddMonths(int months)
        {
            StarDate dt = this;
            dt.Month += months;
            return dt;
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

        // Returns the StarDate resulting from adding the given number of
        // 100-nanosecond _ticks to this StarDate. The value argument
        // is permitted to be negative.
        //
        public StarDate AddTicks(long value)
        {
            BigInteger ticks = dateData;
            return new StarDate((ticks + value), errorData, TimeZone);
        }

        // Returns the StarDate resulting from adding the given number of
        // years to this StarDate. The result is computed by incrementing
        // (or decrementing) the Year part of this StarDate by value
        // years. If the month and day of this StarDate is 2/29, and if the
        // resulting Year is not a leap Year, the month and day of the resulting
        // StarDate becomes 2/28. Otherwise, the month, day, and time-of-day
        // parts of the result are the same as those of this StarDate.
        //
        public StarDate AddYears(int value)
        {
            return this + value * YearTime;
        }

        // Compares two StarDate values, returning an integer that indicates
        // their relationship.
        //
        public static int Compare(StarDate t1, StarDate t2)
        {
            BigInteger ticks1 = t1.dateData;
            BigInteger ticks2 = t2.dateData;
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
        //        [ResourceExposure(ResourceScope.None)]
        //        [SuppressUnmanagedCodeSecurity]
        //        [return: MarshalAs(UnmanagedType.Bool)]
        //        internal static extern bool LegacyParseMode();

        //        [DllImport(JitHelpers.QCall, CharSet = CharSet.Unicode)]
        //        [SecurityCritical]
        //        [ResourceExposure(ResourceScope.None)]
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
            return dateData == value.dateData;
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
            throw new NotImplementedException();
        }

        // A version of ToBinary that uses the real representation and does not adjust local times. This is needed for
        // scenarios where the serialized data must maintain compatability
        internal static StarDate FromBinaryRaw(Int64 dateData)
        {
            BigInteger ticks = dateData & (Int64)ticksMask;
            if (ticks < MinTicks || ticks > MaxTicks)
                throw new ArgumentException(); //); //Environment.GetResourceString("Argument_StarDateBadBinaryData"), "dateData");
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
        public static StarDate FromOADate(double d)
        {
            return (StarDate)DateTime.FromOADate(d);
        }

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
            throw new NotImplementedException();
        }

        // Return the underlying data, without adjust local times to the right time zone. Needed if performance
        // or compatability are important.
        internal Int64 ToBinaryRaw()
        {
            return (Int64)dateData;
        }

        // Returns the hash code for this StarDate.
        //
        public override int GetHashCode()
        {
            BigInteger ticks = dateData;
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

                int year, month, day;
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
        //[ResourceExposure(ResourceScope.None)]
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
                return dateData + offset.Ticks;
            }
            set
            {
                //a = d + o
                //a - o = d
                dateData = value - offset.Ticks;
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
                dt.error = StarDate.HourTime * 12;
                return dt;
            }
        }

        //returns the margin of error for a time

        public Time error
        {
            get
            {
                return new Time(errorData);
            }

            private set
            {
                errorData = value.Ticks;
            }
        }

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

        //returns the amount of years since the Big Bang

        public long fullyear
        {
            get { return this.Atomic / StarDate.AverageYear; }
            internal set
            {
                long diff = value - this.fullyear;
                this.Atomic += diff * StarDate.AverageYear;
            }
        }

        //returns the amount of quadrillion years since the Big Bang (currently zero)

        public int quadrillion
        {
            get
            {
                return GetDatePart(DatePartQuadrillion);
            }
            internal set
            {
                int diff = value - this.quadrillion;
                this.Atomic += diff * StarDate.tr * 1000;
            }
        }

        //returns the amount of trillion years since the Big Bang (currently zero)

        public int trillion
        {
            get
            {
                return GetDatePart(DatePartTrillion);
            }
            internal set
            {
                int diff = value - this.trillion;
                this.Atomic += diff * StarDate.tr;
            }
        }

        //returns the amount of billion years since the Big Bang (currently 14)

        public int billion
        {
            get
            {
                return GetDatePart(DatePartBillion);
            }
            internal set
            {
                int diff = value - this.billion;
                this.Atomic += diff * StarDate.b;
            }
        }

        //returns millions of years not included in billion or higher (currently zero)

        public int million
        {
            get
            {
                return GetDatePart(DatePartMillion);
            }
            internal set
            {
                int diff = value - this.million;
                this.Atomic += diff * StarDate.m;
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

        public Time offset
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

            internal set
            {
                this.TimeZone = this.TimeZone.OffsetClone(value);
            }
        }

        //returns DateTime equivalent

        public DateTime DateTime
        {
            get
            {
                DateTime dt = new DateTime((long)(dateData - NetStart));
                DateTime.SpecifyKind(dt, Kind);
                return dt;
            }
        }




        // Returns the Year part of this StarDate. The returned value is an
        // integer between 1 and 1,000,000.

        public int Year
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1 && Contract.Result<int>() <= 1000000);
                return GetDatePart(DatePartYear);
            }
            set
            {
                StarDate dt = new StarDate(Year + 1, Month, Day, Hour, Minute, Second, Millisecond, ExtraTicks);
                this.Atomic = dt.Atomic;
            }
        }

        // Returns the month part of this StarDate. The returned value is an
        // integer between 1 and 12.
        //
        public int Month
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1 && Contract.Result<int>() <= 14);
                return GetDatePart(DatePartMonth);
            }
            set
            {
                int diff = value - this.Month;
                this.Atomic += diff * StarDate.month;
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
                int diff = value - this.WeekOfYear;
                this.Atomic += diff * week;
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
                return GetDatePart(DatePartDayOfYear);
            }
            set
            {
                int diff = value - this.DayOfYear;
                this.Atomic += diff * StarDate.DayTime;
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
                return GetDatePart(DatePartDay);
            }
            set
            {
                int diff = value - this.Day;
                this.Atomic += diff * StarDate.DayTime;
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
                    int h = (int)((AdjustedTicks / TicksPerHour) % 24);
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
                    return (int)((AdjustedTicks / TicksPerHour) % 24);
                }
            }
            set
            {
                int h = value;
                int diff = h - this.Hour;
                this.Atomic += diff * StarDate.HourTime;
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
                return (int)((AdjustedTicks / TicksPerMinute) % 60);
            }
            set
            {
                int h = value;
                int diff = h - this.Minute;
                this.Atomic += diff * StarDate.MinuteTime;
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
                return (int)((AdjustedTicks / TicksPerSecond) % 60);
            }
            set
            {
                int diff = value - this.Second;
                this.Atomic += diff * StarDate.SecondTime;
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
                return (int)((AdjustedTicks / TicksPerMillisecond) % 1000);
            }
            set
            {
                int diff = value - this.Millisecond;
                this.Atomic += diff * StarDate.MillisecondTime;
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
                return (int)((AdjustedTicks % 10000));
            }
            set
            {
                int diff = value - this.ExtraTicks;
                this.dateData += diff;
            }
        }




        // Returns the tick count for this StarDate. The returned value is
        // the number of 100-nanosecond intervals that have elapsed since the rounded date of the Big Bang 
        //
        public BigInteger Ticks
        {
            get
            {
                return dateData;
            }
            set
            {
                this.dateData = value;
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
                return StarCulture.Symbols.GetMonthName(Month);
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

        //returns the symbol of the day

        public string DaySymbol
        {
            get
            {
                return StarCulture.Symbols.GetDayName(DayOfWeek);
            }
        }

        public int Julian
        {
            get
            {
                return ((this - StarDate.julian) / StarDate.DayTime) + 1;
            }

            set
            {
                int diff = value - this.Julian;
                this += diff * StarDate.DayTime;
            }
        }

        //returns Atomic Clock Time

        public Time Atomic
        {
            get
            {
                return new Time(dateData);
            }

            private set
            {
                dateData = value.Ticks;
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

                }
                return formats;
            }

            private set
            {
                formats = value;
            }
        }











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
            return TicksToOADate((long)(AdjustedTicks - ADStart.Ticks));
        }

        public long ToFileTime()
        {
            // Treats the input as local if it is not specified
            return ToUniversalTime().ToFileTimeUtc();
        }

        public long ToFileTimeUtc()
        {
            // Treats the input as universal if it is not specified
            //BigInteger ticks = ((Kind & LocalMask) != 0) ? ToUniversalTime().InternalTicks : this.InternalTicks;

            //if (s_isLeapSecondsSupportedSystem)
            //{
            //    return InternalToFileTime(ticks);
            //}

            //ticks -= FileTimeOffset;
            //if (ticks < 0)
            //{
            //    throw new ArgumentOutOfRangeException(); //(null, ); //Environment.GetResourceString("ArgumentOutOfRange_FileTimeInvalid"));
            //}

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

        public String ToLongDateString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            //////////////Console.WriteLine(sdfi.CultureName);
            return StarDateFormat.Format(this, "D", StarCulture.CurrentCulture);
        }

        public String ToLongTimeString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            //////////////Console.WriteLine(sdfi.CultureName);
            return StarDateFormat.Format(this, "T", StarCulture.CurrentCulture);
        }

        public String ToShortDateString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            //////////////Console.WriteLine(sdfi.CultureName);
            return StarDateFormat.Format(this, "d", StarCulture.CurrentCulture);
        }

        public String ToShortTimeString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            ////////////Console.WriteLine(this.CultureName);
            return StarDateFormat.Format(this, "t", StarCulture.CurrentCulture);
        }



        public String ToString(IFormatProvider provider)
        {
            Contract.Ensures(Contract.Result<String>() != null);
            return StarDateFormat.Format(this, null, StarCulture.GetInstance(provider));
        }

        public String ToString(String format, IFormatProvider provider)
        {
            Contract.Ensures(Contract.Result<String>() != null);
            return StarDateFormat.Format(this, format, StarCulture.GetInstance(provider));
        }

        public StarDate ToUniversalTime()
        {
            return this.ToZone(UTC);
        }

        //I don't know what these methods do and whether to replicate them
        public static Boolean TryParse(String s, out StarDate result)
        {
            try
            {
                result = StarDate.Parse(s);
                return true;
            }
            catch (Exception)
            {
                result = StarDate.Manu;
                return false;
            }
        }

        public static StarDate Parse(string s)
        {
            foreach (string format in StarDate.Formats)
            {
                StarDate dt;
                bool b = TryParse(s, format, out dt);
                if (b)
                {
                    return dt;
                }
            }
            throw new Exception();
        }

        private static bool TryParse(string s, string format, out StarDate dt)
        {
            throw new NotImplementedException();
        }




        /// <internalonly/>
        bool IConvertible.ToBoolean(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Boolean"));
        }

        /// <internalonly/>
        char IConvertible.ToChar(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Char"));
        }

        /// <internalonly/>
        sbyte IConvertible.ToSByte(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "SByte"));
        }

        /// <internalonly/>
        byte IConvertible.ToByte(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Byte"));
        }

        /// <internalonly/>
        short IConvertible.ToInt16(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Int16"));
        }

        /// <internalonly/>
        ushort IConvertible.ToUInt16(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "UInt16"));
        }

        /// <internalonly/>
        int IConvertible.ToInt32(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Int32"));
        }

        /// <internalonly/>
        uint IConvertible.ToUInt32(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "UInt32"));
        }

        /// <internalonly/>
        long IConvertible.ToInt64(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Int64"));
        }

        /// <internalonly/>
        ulong IConvertible.ToUInt64(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "UInt64"));
        }

        /// <internalonly/>
        float IConvertible.ToSingle(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Single"));
        }

        /// <internalonly/>
        double IConvertible.ToDouble(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Double"));
        }

        /// <internalonly/>
        Decimal IConvertible.ToDecimal(IFormatProvider provider)
        {
            throw new InvalidCastException(); //Environment.GetResourceString("InvalidCast_FromTo", "StarDate", "Decimal"));
        }

        /// <internalonly/>
        //StarDate IConvertible.ToStarDate(IFormatProvider provider)
        //{
        //    return this;
        //}

        /// <internalonly/>
        Object IConvertible.ToType(Type type, IFormatProvider provider)
        {
            throw new NotImplementedException(); //return Convert.DefaultToType((IConvertible)this, type, provider);
        }

        public void GetObjectData(SerializationInfo info, StreamingContext context)
        {
            throw new NotImplementedException();
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


        public static StarDate Between(StarDate dt1, StarDate dt2)
        {
            if (dt1 > dt2)
            {
                return Between(dt2, dt1);
            }
            dt1 = dt1 - dt1.error;
            dt2 = dt2 + dt2.error;
            Time error = (dt2 - dt1) / 2;
            dt1 += error;
            dt1.error = error;
            if (dt1.TimeZone != dt2.TimeZone)
            {
                dt1.TimeZone = UTC;
            }
            return dt1;
        }



        private StarDate(SerializationInfo serializationInfo, StreamingContext streamingContext)
        {
            throw new NotImplementedException();
        }


        private static StarDate AbstractDate(BigInteger bigInteger, int v, StarZone uTC)
        {
            StarDate dt = new StarDate();
            dt.dateData = bigInteger;
            dt.errorData = v;
            dt._timeZone = UTC;
            return dt;
        }

        public DateTime ToDateTime(IFormatProvider provider)
        {
            return DateTime;
        }

        TypeCode IConvertible.GetTypeCode()
        {
            throw new NotImplementedException();
        }

        DateTime IConvertible.ToDateTime(IFormatProvider provider)
        {
            return DateTime;
        }

        string IConvertible.ToString(IFormatProvider provider)
        {
            return ToString(provider);
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

        public static implicit operator DateTime(StarDate dt)
        {
            return dt.DateTime;
        }

        public static implicit operator string(StarDate dt)
        {
            return dt.ToString();
        }

        public static implicit operator StarDate(DateTime v)
        {
            return new StarDate(v);
        }

    }
}