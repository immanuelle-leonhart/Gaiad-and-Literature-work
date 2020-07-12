using StarCalendar;
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Diagnostics.Contracts;
using System.Globalization;
using System.IO;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;
//using CultureInfo = System.Globalization.CultureInfo;
//using Calendar = System.Globalization.Calendar;

namespace StarCalendar
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
        "ddd"               short weekday StarName (abbreviation)     Mon
        "dddd"              full weekday StarName                     Monday
        "dddd*"             full weekday StarName                     Monday


        "M"     "0"         Month w/o leading zero                2
        "MM"    "00"        Month with leading zero               02
        "MMM"               short Month StarName (abbreviation)       Feb
        "MMMM"              full Month StarName                       Febuary
        "MMMM*"             full Month StarName                       Febuary

        "y"     "0"         two digit Year (Year % 100) w/o leading zero           0
        "yy"    "00"        two digit Year (Year % 100) with leading zero          00
        "yyy"   "D3"        Year                                  2000
        "yyyy"  "D4"        Year                                  2000
        "yyyyy" "D5"        Year                                  2000
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
        "d"                 short date                              culture-specific                        10/31/1999
        "D"                 long data                               culture-specific                        Sunday, October 31, 1999
        "f"                 full date (long date + short time)      culture-specific                        Sunday, October 31, 1999 2:00 AM
        "F"                 full date (long date + long time)       culture-specific                        Sunday, October 31, 1999 2:00:00 AM
        "g"                 general date (short date + short time)  culture-specific                        10/31/1999 2:00 AM
        "G"                 general date (short date + long time)   culture-specific                        10/31/1999 2:00:00 AM
        "m"/"M"             Month/Day date                          culture-specific                        October 31
(G)     "o"/"O"             Round Trip XML                          "yyyy-MM-ddTHH:mm:ss.fffffffK"          1999-10-31 02:00:00.0000000Z
(G)     "r"/"R"             RFC 1123 date,                          "ddd, dd MMM yyyy HH':'mm':'ss 'GMT'"   Sun, 31 Oct 1999 10:00:00 GMT
(G)     "s"                 Sortable format, based on ISO 8601.     "yyyy-MM-dd'T'HH:mm:ss"                 1999-10-31T02:00:00
                                                                    ('T' for local time)
        "t"                 short time                              culture-specific                        2:00 AM
        "T"                 long time                               culture-specific                        2:00:00 AM
(G)     "u"                 Universal time with sortable format,    "yyyy'-'MM'-'dd HH':'mm':'ss'Z'"        1999-10-31 10:00:00Z
                            based on ISO 8601.
(U)     "U"                 Universal time with full                culture-specific                        Sunday, October 31, 1999 10:00:00 AM
                            (long date + long time) format
                            "y"/"Y"             Year/Month day                          culture-specific                        October, 1999

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

        //internal static readonly bool s_isLeapSecondsSupportedSystem = SystemSupportLeapSeconds();

        private static readonly int[] DaysToMonth365 = {
            0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
        private static readonly int[] DaysToMonth366 = {
            0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};

        //public static readonly StarDate MinValue = new StarDate(MinTicks, DateTimeKind.Unspecified);
        //public static readonly StarDate MaxValue = new StarDate(MaxTicks, DateTimeKind.Unspecified);
        //private readonly StarZone local;
        //private static readonly StarZone uTC;
        //private readonly BigInteger netStart;
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
        //               12/31/9999 23:59:59.9999999
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
        private static bool LongDefault = false;

        //private int extraTicks;

        //private int julian;

        //private StarZone z;

        public StarDate TickTimeZoneConvert(StarZone z)
        {
            return new StarDate(Year, Month, Day, Hour, Minute, Second, Millisecond);
        }

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

        //private Time atomic1;
        //private Time error1;
        //private StarZone uTC1;

        //public static StarCulture English = StarCulture.InvariantCulture;
        //public static StarZone Local = StarZone.Local;

        internal static int DayFromMonth(int day)
        {
            day--;
            day %= 7;
            day++;
            return day;
        }

        public static StarDate StarHanukkah()
        {
            return new StarDate(GregHanukkah());
        }

        private static void DemonstrateLanguage(StarCulture lang, string format)
        {
            //StarDate.SetFormat("numeric");
            StarDate dt = StarDate.maya;
            dt -= 379 * StarDate.DayTime;
            int i = 0;
            while (dt < StarDate.maya)
            {
                dt += StarDate.DayTime;
                i++;
                //////////Console.WriteLine(dt.ToString(lang, format));
            }
        }

        internal static void SetFormat(string v)
        {
            DefaultFormat = v;
        }

        public static void MakeChart(string v)
        {
            StarDate.MakeChart(v, DateTime.Now.Year);
        }

        public static void MakeChart(string v, int gregyear)
        {
            StreamWriter chart = new StreamWriter(v + "StarCalendar.csv");
            StarDate dt = StarDate.FromGreg(gregyear, 6, 1);
            int staryear = dt.Year;
            dt = new StarDate(staryear, 1, 1);
            StarDate end = StarDate.FromGreg(gregyear + 1, 1, 1);
            string gregday = "Day of the Gregorian Month";
            string gregmonthname = "Gregorian Month PlanetName";
            string gregmonthnumber = "Gregorian Month Number";
            string g_year = "Gregorian Year";
            string gregdayofyear = "Gregorian Day of Year";
            string weekday = "Day of the Week";
            string comma = ",";
            string starday = "Day of the Star Month";
            string starmonthname = "Star Month PlanetName";
            string starmonthnumber = "Star Month Number";
            string StarYear = "Star Year";
            string Stardayofyear = "Star Day of Year";
            string[] months = new string[] { "None", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" };
            string output = g_year + comma + gregmonthname + comma + gregmonthnumber + comma + gregday + comma + gregdayofyear + comma + weekday + comma + StarYear + comma + starmonthname + comma + starmonthnumber + comma + starday + comma + Stardayofyear;
            while (dt <= end)
            {
                //////////Console.WriteLine(output);
                chart.WriteLine(output);
                DateTime g = dt.DateTime;
                gregday = g.Day.ToString();
                gregmonthname = months[g.Month];
                gregmonthnumber = g.Month.ToString();
                g_year = g.Year.ToString();
                gregdayofyear = g.DayOfYear.ToString();
                weekday = g.DayOfWeek.ToString();
                starday = dt.Day.ToString();
                starmonthname = dt.MonthName;
                starmonthnumber = dt.Month.ToString();
                StarYear = dt.Year.ToString();
                Stardayofyear = dt.DayOfYear.ToString();
                output = g_year + comma + gregmonthname + comma + gregmonthnumber + comma + gregday + comma + gregdayofyear + comma + weekday + comma + StarYear + comma + starmonthname + comma + starmonthnumber + comma + starday + comma + Stardayofyear;
                dt += StarDate.DayTime;
            }
            chart.Flush();
            chart.Close();
        }

        internal static StarDate AbstractDate(Time timeSpanInfo)
        {
            StarDate dt = new StarDate(timeSpanInfo);

            dt.TimeZone = StarZone.Local;
            //dt.arraylength = 10;
            dt.errorData = 0;
            return dt;
        }

        //internal static string Time(Dictionary<string, int> data)
        //{
        //    string dt = "";
        //    try
        //    {
        //        dt = data["hour"] + ":" + data["Minute"];
        //        try
        //        {
        //            dt = dt + ":" + data["second"];
        //            try
        //            {
        //                dt = dt + ":" + data["Millisecond"];
        //                try
        //                {
        //                    dt = dt + ":" + data["_ticks"];
        //                }
        //                catch (KeyNotFoundException)
        //                {

        //                }
        //            }
        //            catch (KeyNotFoundException)
        //            {

        //            }
        //        }
        //        catch (KeyNotFoundException)
        //        {

        //        }
        //    }
        //    catch (KeyNotFoundException)
        //    {

        //    }
        //    return dt;
        //}

        private static string GregHoliday(DateTime dateTime)
        {
            throw new NotImplementedException();
        }

        public static StarDate StarHanukkah(DateTime dt)
        {
            return new StarDate(GregHanukkah(dt));
        }

        public static StarDate StarHanukkah(StarDate dt)
        {
            return new StarDate(GregHanukkah(dt));
        }

        internal static StarDate Parse(string v)
        {
            throw new NotImplementedException();
        }

        public static DateTime GregHanukkah()
        {
            return GregHanukkah(DateTime.Now);
        }

        public static DateTime GregHanukkah(DateTime now)
        {
            System.Globalization.Calendar HebCal = new HebrewCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 11, 1);
            int hebyear = HebCal.GetYear(now);
            DateTime Hanukkah = new DateTime(hebyear, 3, 25, new HebrewCalendar());
            return Hanukkah;
        }


        public static DateTime GregHanukkah(StarDate dt)
        {
            DateTime o = new StarDate(dt.Year, 12, 1).DateTime;
            return GregHanukkah(o);
        }



        //public StarZone _timeZone;


        internal static StarDate MathFromGreg(int[] v)
        {
            return MathFromGreg(v[0], v[1], v[2]);
        }






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
            internal set
            {
                int h = value;
                int diff = h - this.Hour;
                this.atomic += diff * StarDate.HourTime;
            }
        }


        public static StarDate Now
        {
            get { return new StarDate(DateTime.UtcNow, StarZone.Local); }
            //internal set
            //{
            //    now = value;
            //}
        }
        public static StarDate UtcNow
        {
            get
            {
                return new StarDate(DateTime.UtcNow, StarZone.UTC);
            }
        }
        public long fullyear
        {
            get { return this.atomic / StarDate.AverageYear; }
            internal set
            {
                long diff = value - this.fullyear;
                this.atomic += diff * StarDate.AverageYear;
            }
        }

        internal static bool LegacyParseMode()
        {
            throw new NotImplementedException();
        }

        public int quadrillion
        {
            get
            {
                return GetDatePart(DatePartQuadrillion);
            }
            internal set
            {
                int diff = value - this.quadrillion;
                this.atomic += diff * StarDate.tr * 1000;
            }
        }

        public int trillion
        {
            get
            {
                return GetDatePart(DatePartTrillion);
            }
            internal set
            {
                int diff = value - this.trillion;
                this.atomic += diff * StarDate.tr;
            }
        }

        public int billion
        {
            get
            {
                return GetDatePart(DatePartBillion);
            }
            internal set
            {
                int diff = value - this.billion;
                this.atomic += diff * StarDate.b;
            }
        }
        public int million
        {
            get
            {
                return GetDatePart(DatePartMillion);
            }
            internal set
            {
                int diff = value - this.million;
                this.atomic += diff * StarDate.m;
            }
        }

        public int Year
        {
            get
            {
                return GetDatePart(DatePartYear);
            }
            internal set
            {
                StarDate dt = new StarDate(Year + 1, Month, Day, Hour, Minute, Second, Millisecond, ExtraTicks);
                this.atomic = dt.atomic;
                //throw new NotImplementedException(lololololol);
            }
        }


        public int Millisecond
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 0);
                Contract.Ensures(Contract.Result<int>() < 1000);
                return (int)((AdjustedTicks / TicksPerMillisecond) % 1000);
            }
            internal set
            {
                int diff = value - this.Millisecond;
                this.atomic += diff * StarDate.MillisecondTime;
            }
        }
        //public BigInteger Ticks
        //{
        //    get { return this.atomic._ticks; }
        //    internal set
        //    {
        //        this.atomic._ticks = value;
        //    }
        //}
        public string MonthName
        {
            get { return StarCulture.CurrentCulture.month(this.Month); }
            internal set
            {
                switch (value)
                {
                    case "Sagittarius":
                        this.Month = 1;
                        break;
                    case "Capricorn":
                        this.Month = 2;
                        break;
                    case "Aquarius":
                        this.Month = 3;
                        break;
                    case "Pisces":
                        this.Month = 4;
                        break;
                    case "Aries":
                        this.Month = 5;
                        break;
                    case "Taurus":
                        this.Month = 6;
                        break;
                    case "Gemini":
                        this.Month = 7;
                        break;
                    case "Karkino":
                        this.Month = 8;
                        break;
                    case "Leo":
                        this.Month = 9;
                        break;
                    case "Virgo":
                        this.Month = 10;
                        break;
                    case "Libra":
                        this.Month = 11;
                        break;
                    case "Scorpio":
                        this.Month = 12;
                        break;
                    case "Ophiuchus":
                        this.Month = 13;
                        break;
                    case "Horus":
                        this.Month = 14;
                        break;
                    default:
                        break;
                }
            }
        }

        private int MonthNumberFromName(string value)
        {
            throw new NotImplementedException();
        }

        //public StarZone TimeZone
        //{
        //    get
        //    {
        //        return this.TimeZone;
        //    }
        //    set
        //    {
        //        this.TimeZone = value;
        //    }
        //}

        public Time Radio
        {
            get
            {
                return this.TimeZone.ToRadio(this.atomic);
            }

            internal set
            {
                this.atomic = this.TimeZone.FromRadio(value);
            }
        }
        public Time Terra
        {
            get
            {
                return this.TimeZone.ToTerran(this.atomic);
            }

            internal set
            {
                this.atomic = this.TimeZone.FromTerran(value);
            }
        }
        public Time Arrival
        {
            get
            {
                return this.TimeZone.ToArrival(this.atomic);
            }

            internal set
            {
                this.atomic = this.TimeZone.FromArrival(value);
            }
        }

        public bool IsTerran
        {
            get
            {
                return this.TimeZone.IsTerran;
            }
        }
        public bool SupportsDaylightSavingTime
        {
            get
            {
                return this.TimeZone.SupportsDaylightSavingTime;
            }

        }

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

        //public bool HasTimeZone
        //{
        //    get
        //    {
        //        return this._timeZone.HasTimeZone;
        //    }

        //}

        public StarDate(DateTime dt)
        {
            dateData = NetStart + dt.Ticks;
            errorData = 0;
            if (dt.Kind == DateTimeKind.Local)
            {
                this._timeZone = Local;
                dateData -= Local.Offset(dt).Ticks;
            }
            else
            {
                this._timeZone = UTC;
            }

        }

        public StarDate EasterDate()
        {
            return StarEaster((int)this.gregyear());
        }

        internal static StarDate StarEaster(int year)
        {
            DateTime easter = StarDate.GregEaster(year);
            return new StarDate(easter);
        }

        internal static StarDate StarThanksgiving(int year)
        {
            DateTime Thanksgiving = StarDate.GregThanksgiving(year);
            return new StarDate(Thanksgiving);
        }



        internal bool Easter()
        {
            return this.today() == this.EasterDate();
        }

        private StarDate today()
        {
            throw new NotImplementedException();
        }

        internal static StarDate MathFromGreg(int v1, int v2, int v3)
        {
            return MathFromGreg(v1, v2, v3, 0, 0, 0, 0);
        }

        //internal string Stored()
        //{
        //    return this.Year + "-" + this.Month() + "-" + this.day();
        //}

        internal static StarDate GregParse(string[] data)
        {
            throw new NotImplementedException();
        }

        internal void AddTime(string[] data)
        {
            throw new NotImplementedException();
        }

        //    internal string teststring()
        //    {
        //        //if (this == ADStart)
        //        //{
        //        //    return new int[] { 1, 1, 1 };
        //        //}
        //        //else
        //        //{
        //            Time t = this - ADStart;
        //            int DaysPerYear = 365;
        //            // Number of days in 4 years
        //            int DaysPer4Years = DaysPerYear * 4 + 1;       // 1461
        //                                                           // Number of days in 100 years
        //            int DaysPer100Years = DaysPer4Years * 25 - 1;  // 36524
        //                                                           // Number of days in 400 years
        //            int DaysPer400Years = DaysPer100Years * 4 + 1; // 146097
        //                                                           //Time q = DaysPer400Years * StarDate.DayTime;
        //                                                           //Time s = DaysPer100Years * StarDate.DayTime;
        //                                                           //Time l = DaysPer4Years * StarDate.DayTime;
        //                                                           //Time y = DaysPerYear * StarDate.DayTime;
        //            int[] DaysToMonth365 = {
        //                0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
        //            int[] DaysToMonth366 = {
        //                0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};

        //            ////////////Console.WriteLine("testing");

        //            ////////////Console.WriteLine(t);

        //            int days = t / StarDate.DayTime;
        //            ////////////Console.WriteLine("days from netstart = " + days);

        //            int q = days / DaysPer400Years;
        //            int qmod = days % DaysPer400Years;
        //            ////////////Console.WriteLine(q);
        //            ////////////Console.WriteLine(qmod);
        //            if (qmod < 0)
        //            {
        //                qmod = DaysPer400Years + qmod;
        //                q--;
        //            }
        //            ////////////Console.WriteLine(q);
        //            ////////////Console.WriteLine(qmod);
        //            int s = qmod / DaysPer100Years;
        //            int smod = qmod % DaysPer100Years;
        //            int l = smod / DaysPer4Years;
        //            int lmod = smod % DaysPer4Years;
        //            int y = lmod / DaysPerYear;
        //            int ymod = lmod % DaysPerYear;
        //            ////////////Console.WriteLine(s);
        //            ////////////Console.WriteLine(l);
        //            ////////////Console.WriteLine(y);
        //            int m = 500;
        //            int yd = ymod;
        //            int d = 500;
        //            int Year = 400 * q + 100 * s + 4 * l + y;
        //            //if (Year < 1)
        //            //{
        //            //    Year--;
        //            //}
        //            if (s == 4)
        //            {
        //                s = 3;
        //                l = 24;
        //                y = 3;
        //                m = 11;
        //                d = 31;
        //                Year--;
        //            }
        //            else if (GregLeap(Year) == true)
        //            {
        //                int i = 0;
        //                bool found = false;
        //                while (!found)
        //                {
        //                    ////////////Console.WriteLine(DaysToMonth366[i]);
        //                    if (DaysToMonth366[i] > yd)
        //                    {
        //                        m = i - 1;
        //                        found = true;
        //                        d = yd - DaysToMonth366[m] + 1;
        //                    }
        //                    else
        //                    {
        //                        i++;
        //                    }
        //                }
        //            }
        //            else
        //            {
        //                ////////////Console.WriteLine(GregLeap(Year));
        //                int i = 0;
        //                bool found = false;
        //                while (!found)
        //                {
        //                    ////////////Console.WriteLine(DaysToMonth366[i]);
        //                    if (DaysToMonth365[i] > yd)
        //                    {
        //                        m = i - 1;
        //                        found = true;
        //                        d = yd - DaysToMonth365[m] + 1;
        //                    }
        //                    else
        //                    {
        //                        i++;
        //                    }
        //                }
        //            }
        //        ////////////Console.WriteLine(Year + " " + m + " " + d + " ");
        //        //throw new NotImplementedException();
        //        if (this > ADStart)
        //        {
        //            //////////Console.WriteLine("TEST");
        //            Year++;
        //        }
        //        m++;
        //            int[] vs = new int[] { Year, m, d };
        //        return Year + "-" + m + "-" + d;


        //}

        private long gregyear()
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

        public StarDate(Time t) : this()
        {
            this.atomic = t;
            this.TimeZone = StarZone.Local;
        }

        //public StarDate(int v) : this()
        //{
        //    this.atomic = new Time(v);
        //    this._timeZone = StarZone.Local;
        //}

        public StarDate(BigInteger v, StarZone Zone) : this(v)
        {
            this.atomic = new Time(v) + ADStart.atomic;
            this.TimeZone = Zone;
            //this.metadata = new StarData(Zone);
        }

        //internal long DayOfYear()
        //{
        //    return this.LocalData()["day of Year"];
        //}

        //public StarDate(DateTime dt, StarZone zone) : this(dt)
        //{
        //    this.atomic = new Time(v) + ADStart.atomic;
        //}

        public StarDate(DateTime utcNow, StarZone zone) : this(utcNow)
        {
            //this.atomic = ADStart.atomic + new Time(dt.Ticks);
            this.TimeZone = zone;
            //this.metadata = new StarData(zone);
        }

        private static StarDate AnnoCosmos(params long[] vs)
        {
            throw new NotImplementedException();
            //long[] data = new long[] { 0, 0, 0, 0, 0, 0, 0, 0 };
            //int i = 0;
            //int n = vs.Length;
            //if (n > 8)
            //{
            //    n = 8;
            //}
            //while (i < n)
            //{
            //    data[i] = vs[i];
            //    i++;
            //}
            //this.atomic = new Time(0);
            //long years = data[0];
            //long cycle_78 = years / 78;
            //this.atomic += cycle_78 * StarDate.Seventy_Eight;
            //years %= 78;
            //long cycle_6 = years / 6;
            //this.atomic += cycle_6 * StarDate.Sixyear;
            //years %= 6;
            //long cycle_1 = years;
            //this.atomic += cycle_1 * StarDate.Year;
            //data[1]--;
            //data[2]--; //The 1st of a Month is actually zero days, so subtract one from the day, same for months
            //this.atomic += data[1] * StarDate.Month + data[2] * StarDate.DayTime + data[3] * StarDate.HourTime + data[4] * StarDate.MinuteTime + data[5] * StarDate.SecondTime + data[6] * StarDate.MillisecondTime + new Time(data[7]);
            //switch (n)
            //{
            //    case 1:
            //        this.error = StarDate.Year;
            //        break;
            //    case 2:
            //        this.error = StarDate.Month;
            //        break;
            //    case 3:
            //        this.error = StarDate.DayTime;
            //        break;
            //    case 4:
            //        this.error = StarDate.HourTime;
            //        break;
            //    case 5:
            //        this.error = StarDate.MinuteTime;
            //        break;
            //    case 6:
            //        this.error = StarDate.SecondTime;
            //        break;
            //    case 7:
            //        this.error = StarDate.MillisecondTime;
            //        break;
            //    case 8:
            //    default:
            //        this.error = new Time(0);
            //        break;
            //}

            ////assign timezones

            //this._timeZone = StarZone.UTC;

            ////assign notes

            //this.note = "";
        }


        //public StarDate(params long[] vs)
        //{
        //    long[] data = new long[] { 0, 0, 0, 0, 0, 0, 0, 0 };
        //    int i = 0;
        //    int n = vs.Length;
        //    if (n > 8)
        //    {
        //        n = 8;
        //    }
        //    while (i < n)
        //    {
        //        data[i] = vs[i];
        //        i++;
        //    }
        //    //this = StarDate.manu;
        //    dateData = StarDate.b.Ticks;
        //    errorData = 0;
        //    _timeZone = Local;
        //    long years = data[0];
        //    long cycle_78 = years / 78;
        //    this.atomic += cycle_78 * StarDate.Seventy_Eight;
        //    years %= 78;
        //    long cycle_6 = years / 6;
        //    this.atomic += cycle_6 * StarDate.Sixyear;
        //    years %= 6;
        //    long cycle_1 = years;
        //    this.atomic += cycle_1 * StarDate.Year;
        //    data[1]--;
        //    data[2]--; //The 1st of a Month is actually zero days, so subtract one from the day, same for months
        //    this.atomic += data[1] * StarDate.month + data[2] * StarDate.DayTime + data[3] * StarDate.HourTime + data[4] * StarDate.MinuteTime + data[5] * StarDate.SecondTime + data[6] * StarDate.MillisecondTime + new Time(data[7]);


        //    //this.arraylength = n;
        //    switch (vs.Length)
        //    {
        //        case 1:
        //            errorData = StarDate.Year.Ticks;
        //            break;
        //        case 2:
        //            errorData = StarDate.month.Ticks;
        //            break;
        //        case 3:
        //            errorData = StarDate.DayTime.Ticks;
        //            break;
        //        case 4:
        //            errorData = StarDate.HourTime.Ticks;
        //            break;
        //        case 5:
        //            errorData = StarDate.MinuteTime.Ticks;
        //            break;
        //        case 6:
        //            errorData = StarDate.SecondTime.Ticks;
        //            break;
        //        case 7:
        //            errorData = StarDate.MillisecondTime.Ticks;
        //            break;
        //        case 8:
        //        default:
        //            errorData = 0;
        //            break;
        //    }
        //}

        public StarDate(Time t, StarZone zone) : this(t)
        {
            this.atomic = t;
            this.TimeZone = zone;
        }

        //internal StarDate(DateTime dt, StarData local) : this(dt)
        //{
        //    //this.atomic = dt;
        //    this.metadata = local;
        //}

        //public static StarDate Now()
        //{
        //    return new StarDate(DateTime.UtcNow);
        //}

        //public static StarDate UTCNow()
        //{
        //    return new StarDate(DateTime.UtcNow, StarZone.UTC);
        //}

        int IComparable<StarDate>.CompareTo(StarDate other)
        {
            throw new NotImplementedException();
        }

        bool IEquatable<StarDate>.Equals(StarDate other)
        {
            throw new NotImplementedException();
        }

        public static StarDate operator +(StarDate d, Time t)
        {
            StarDate dt = d;
            dt.atomic += t;
            return dt;
        }

        public static StarDate operator ++(StarDate dt)
        {
            return dt + DayTime;
        }

        public static StarDate operator --(StarDate dt)
        {
            return dt - DayTime;
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
                    //long Year = long.Parse(parsedinput[1]);
                    //int Month = int.Parse(parsedinput[2]);
                    //int day = int.Parse(parsedinput[3]);
                    int i = 1;
                    long[] vs = new long[] { 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
                    while (i < parsedinput.Length)
                    {
                        vs[i - 1] = long.Parse(parsedinput[i]);
                        i++;
                    }
                    return AnnoCosmos(vs);
                    //new StarDate(vs);
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
                    throw new NotImplementedException();
                }
                else if (modifier == "BET")
                {
                    try
                    {
                        StarDate dt1 = StarDate.GregParse(parsedinput[1] + " " + parsedinput[2] + " " + parsedinput[3]);
                        StarDate dt2 = StarDate.GregParse(parsedinput[5] + " " + parsedinput[6] + " " + parsedinput[7]);
                        return between(dt1, dt2);
                    }
                    catch (IndexOutOfRangeException)
                    {
                        return between(StarDate.FromGreg(int.Parse(parsedinput[1])), StarDate.FromGreg(int.Parse(parsedinput[3])));
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
                        dt = DateTime.Parse(new_input);
                    }
                    catch (FormatException)
                    {
                        try
                        {
                            dt = DateTime.Parse(parsedinput[1] + " " + parsedinput[2] + " " + parsedinput[3]);
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
                                    //////////Console.WriteLine(v);
                                    int year = int.Parse(v);
                                    return StarDate.FromGreg(year);
                                }
                                catch (FormatException)
                                {
                                    //////////Console.WriteLine(input);
                                    if ((parsedinput[1] == "AND"))
                                    {
                                        StarDate a = StarDate.FromGreg(int.Parse(parsedinput[0]));
                                        StarDate b = StarDate.FromGreg(int.Parse(parsedinput[2]));
                                        return between(a, b);
                                    }
                                    throw new InvalidOperationException();
                                    throw new NotImplementedException();
                                    //return StarDate.manu;
                                }
                            }

                        }
                    }
                    //throw new NotImplementedException();
                    StarDate date = new StarDate(dt);
                    //date.addModifier(modifier);
                    return date;
                }
            }
        }



        private static long BCParse(string[] parsedinput)
        {
            int i = 0;
            while (i < parsedinput.Length)
            {
                //////////Console.WriteLine(i + " " + parsedinput[i++]);
            }
            return long.Parse(parsedinput[0]);
            throw new NotImplementedException();
        }

        private static StarDate FromGreg(int year)
        {
            StarDate dt1 = StarDate.FromGreg(year, 01, 01);
            StarDate dt2 = StarDate.FromGreg(year, 12, 31);
            return StarDate.between(dt1, dt2);
        }

        private static StarDate between(StarDate dt1, StarDate dt2)
        {
            Time error = (dt1 - dt2) / 2;
            Time time = (dt1.atomic + dt2.atomic) / 2;
            StarDate dt = new StarDate(time);
            dt.adderror(error);
            return dt;
        }

        private void adderror(Time error)
        {
            this.error = error;
        }

        //private void addModifier(string modifier)
        //{
        //    this.Note = modifier;
        //}

        internal DateTime DateTime
        {
            get
            {
                DateTime dt = new DateTime((long)(this - ADStart)._ticks);
                DateTime.SpecifyKind(dt, Kind);
                return dt;
            }
        }

        public static StarDate operator -(StarDate d, Time t)
        {
            StarDate dt = d;
            dt.atomic -= t;
            return dt;
        }

        //public static Time operator -(StarDate d1, StarDate d2)
        //{
        //    return d1.atomic - d2.atomic;
        //}

        //public static Time operator -(DateTime d1, StarDate d2)
        //{
        //    return new StarDate(d1) - d2;
        //}

        //public static Time operator -(StarDate d1, DateTime d2)
        //{
        //    return d1 - new StarDate(d2);
        //}

        public static bool operator ==(StarDate dt1, StarDate dt2)
        {
            if (dt1.atomic == dt2.atomic)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static bool operator !=(StarDate dt1, StarDate dt2)
        {
            throw new NotImplementedException();
        }

        public static bool operator <(StarDate dt1, StarDate dt2)
        {
            return dt1.atomic < dt2.atomic;
        }

        public static bool operator >(StarDate dt1, StarDate dt2)
        {
            return dt1.atomic > dt2.atomic;
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

        public override string ToString()
        {
            return this.ToString(StarCulture.CurrentCulture);
        }

        public string ToString(StarCulture local)
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

        public string ToString(StarCulture local, string format)
        {
            return local.StarDateString(this, format);
        }

        //private bool IsHoliday()
        //{
        //    return this.GetHoliday() != null;
        //}

        //private int billion()
        //{
        //    return this.LocalData()["b"];
        //}

        //public Time TimeOfDay()
        //{
        //    return this.atomic % StarDate.DayTime;
        //}

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
                ////////Console.WriteLine("Days Since Manu = " + n);
                //Logic Error is here
                ////////Console.WriteLine(DaysPerAverageYear);
                ////////Console.WriteLine(n / DaysPerAverageYear);
                //////////Console.WriteLine()
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
                if (part == DatePartDayOfWeek) return d % 7;
                if (part == DatePartMonth) return (d / 28) + 1;
                if (part == DatePartDay) return (d % 28);
                else throw new ArgumentException();
            }
        }

        // Exactly the same as GetDatePart(int part), except computing all of
        // Year/month/day rather than just one of them.  Used when all three
        // are needed rather than redoing the computations for each.
        internal void GetDatePart(out int year, out int month, out int day)
        {
            if (IsTerran)
            {
                Int64 n = (long)(AdjustedTicks / TicksPerDay);
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
                month = (d / 28) + 1;
                day = (d % 28);
            }
            else
            {
                throw new NotImplementedException();
            }

        }

        // Returns the day-of-month part of this StarDate. The returned
        // value is an integer between 1 and 31.
        //



        //internal StarData GetKind()
        //{
        //    return this.metadata;
        //}

        internal BigInteger GetTicks()
        {
            return this.atomic._ticks;
        }

        internal StarDate SpecifyKind(StarDate starDate, object local)
        {
            throw new NotImplementedException();
        }

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

        private StarDate addtime(Time time)
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
            throw new NotImplementedException();
        }

        public int getyear()
        {
            throw new NotImplementedException();
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

        public static bool leapbool(long year)
        {
            return year % 6 == 0;
        }

        //public override bool Equals(object obj)
        //{
        //    throw new NotImplementedException();
        //}

        //public override int GetHashCode()
        //{
        //    throw new NotImplementedException();
        //}

        internal static void Test()
        {
            StarDate dt = StarDate.Now;
            ////////////Console.WriteLine(dt);
            bool gab = true;
            while (gab)
            {
                //////////Console.WriteLine(dt);
                dt += StarDate.DayTime;
            }
        }

        public static StarDate FromGreg(int year, int month, int day)
        {
            int hour = 0;
            int min = 0;
            int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour)
        {
            //int hour = 0;
            int min = 0;
            int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min)
        {
            //int hour = 0;
            //int min = 0;
            int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min, int sec)
        {
            //int hour = 0;
            //int min = 0;
            //int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
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

        public static StarDate MathFromGreg(int year, int month, int day, int hour, int min, int sec, int mil)
        {
            ////////////Console.WriteLine(Year + " " + Month + " " + day + " " + hour + " " + sec + " " + mil);
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
            StarDate output = new StarDate(ADStart.atomic);
            output += timespans[0] * DaysPer400Years * StarDate.DayTime;
            output += timespans[1] * DaysPer100Years * StarDate.DayTime;
            output += timespans[2] * DaysPer4Years * StarDate.DayTime;
            output += timespans[3] * DaysPerYear * StarDate.DayTime;
            int days;
            if (leapyear)
            {
                try
                {
                    days = DaysToMonth366[month - 1];
                }
                catch (IndexOutOfRangeException)
                {
                    //////////Console.WriteLine(month - 1);
                    throw new NotImplementedException();
                }
            }
            else
            {
                days = DaysToMonth365[month - 1];
            }
            days += day - 1;
            ////////////Console.WriteLine(days);
            output += days * StarDate.DayTime;
            output += hour * StarDate.HourTime;
            output += min * StarDate.MinuteTime;
            output += sec * StarDate.SecondTime;
            output += mil * StarDate.MillisecondTime;
            return output;
            //throw new NotImplementedException();
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

        public static void testtimespans()
        {
            int i = 401;
            while (i > -415)
            {
                int[] r = StarDate.GregSpans(i--);
                if (i == 0)
                {
                    i--;
                }
            }
        }

        internal static int[] GregSpans(int year)
        {
            if (year < 1)
            {
                year++;
            }
            year--;
            int yearmod = year % 400;
            if (yearmod < 0)
            {
                yearmod += 400;
            }
            int quattro = (year - yearmod) / 400;
            //////////Console.WriteLine" 400mod = " + yearmod);
            //////////Console.WriteLine" 400count = " + quattro);
            int centcount = yearmod / 100;
            yearmod %= 100;
            //////////Console.WriteLine" centcount = " + centcount);
            int leapcount = yearmod / 4;
            yearmod %= 4;
            int yearcount = yearmod;
            //////////Console.WriteLine" q " + quattro + " c +" + centcount + " l +" + leapcount + " y +" + yearcount);
            ////////////Console.WriteLine(" ");
            return new int[] { quattro, centcount, leapcount, yearcount };
        }

        public string MathGregString()
        {
            int[] r = this.MathGregNumbers();
            return r[0] + "-" + r[1] + "-" + r[2];
        }

        public string GregString()
        {
            int[] r = this.GregNumbers();
            return r[0] + "-" + r[1] + "-" + r[2];
        }

        public int[] GregNumbers()
        {
            try
            {
                DateTime dt = this.DateTime;
                return new int[] { dt.Year, dt.Month, dt.Day };
            }
            catch (ArgumentOutOfRangeException)
            {

            }
            catch (OverflowException)
            {

            }
            return MathGregNumbers();
        }


        public int[] MathGregNumbers()
        {
            {
                int DaysPerYear = 365;
                // Number of days in 4 years
                int DaysPer4Years = DaysPerYear * 4 + 1;       // 1461
                                                               // Number of days in 100 years
                int DaysPer100Years = DaysPer4Years * 25 - 1;  // 36524
                                                               // Number of days in 400 years
                int DaysPer400Years = DaysPer100Years * 4 + 1; // 146097
                                                               //Time q = DaysPer400Years * StarDate.DayTime;
                                                               //Time s = DaysPer100Years * StarDate.DayTime;
                                                               //Time l = DaysPer4Years * StarDate.DayTime;
                                                               //Time y = DaysPerYear * StarDate.DayTime;
                int[] DaysToMonth365 = {
                    0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
                int[] DaysToMonth366 = {
                    0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};
                if (this == ADStart)
                {
                    return new int[] { 1, 1, 1 };
                }
                else if (this < ADStart)
                {
                    Time t = this - ADStart;


                    ////////////Console.WriteLine("testing");

                    ////////////Console.WriteLine(t);

                    int days = t / StarDate.DayTime;
                    ////////////Console.WriteLine("days from netstart = " + days);

                    int q = days / DaysPer400Years;
                    int qmod = days % DaysPer400Years;
                    ////////////Console.WriteLine(q);
                    ////////////Console.WriteLine(qmod);
                    if (qmod < 0)
                    {
                        qmod = DaysPer400Years + qmod;
                        q--;
                    }
                    ////////////Console.WriteLine(q);
                    ////////////Console.WriteLine(qmod);
                    int s = qmod / DaysPer100Years;
                    int smod = qmod % DaysPer100Years;
                    int l = smod / DaysPer4Years;
                    int lmod = smod % DaysPer4Years;
                    int y = lmod / DaysPerYear;
                    int ymod = lmod % DaysPerYear;
                    ////////////Console.WriteLine(s);
                    ////////////Console.WriteLine(l);
                    ////////////Console.WriteLine(y);
                    int m = 500;
                    int yd = ymod;
                    int d = 500;
                    int year = 400 * q + 100 * s + 4 * l + y;
                    //if (Year < 1)
                    //{
                    //    Year--;
                    //}
                    if (s == 4)
                    {
                        s = 3;
                        l = 24;
                        y = 3;
                        m = 11;
                        d = 31;
                        year--;
                    }
                    else if (GregLeap(year) == true)
                    {
                        int i = 0;
                        bool found = false;
                        while (!found)
                        {
                            ////////////Console.WriteLine(DaysToMonth366[i]);
                            if (DaysToMonth366[i] > yd)
                            {
                                m = i - 1;
                                found = true;
                                ////////////Console.WriteLine("366");
                                d = yd - DaysToMonth366[m] + 1;
                            }
                            else
                            {
                                i++;
                            }
                        }
                    }
                    else
                    {
                        ////////////Console.WriteLine(GregLeap(Year));
                        int i = 0;
                        bool found = false;
                        while (!found)
                        {
                            ////////////Console.WriteLine(DaysToMonth366[i]);
                            if (DaysToMonth365[i] > yd)
                            {
                                m = i - 1;
                                found = true;
                                d = yd - DaysToMonth365[m] + 1;
                            }
                            else
                            {
                                i++;
                            }
                        }
                    }
                    ////////////Console.WriteLine(Year + " " + m + " " + d + " ");
                    //throw new NotImplementedException();
                    if (d == 0)
                    {
                        throw new NotImplementedException();
                    }
                    m++;
                    if (this > ADStart)
                    {
                        ////////////Console.WriteLine("TEST");
                        year++;
                    }
                    return new int[] { year, m, d };
                }
                else // this > ADStart
                {
                    int year;
                    int t = (this - ADStart) / StarDate.DayTime;
                    int q = t / DaysPer400Years;
                    t %= DaysPer400Years;
                    int s = t / DaysPer100Years;
                    if (s == 4)
                    {
                        year = 1 + 400 * q + 399;
                        return new int[] { year, 12, 31 };
                        throw new NotImplementedException();
                    }
                    t %= DaysPer100Years;
                    int l = t / DaysPer4Years;
                    t %= DaysPer4Years;
                    int y = t / DaysPerYear;
                    var months = DaysToMonth365;
                    year = 1 + 400 * q + 100 * s + 4 * l + y;
                    if (GregLeap(year))
                    {
                        months = DaysToMonth366;
                    }
                    t %= DaysPerYear;


                    int m = 500;
                    int d = 500;

                    int i = 0;
                    bool found = false;
                    while (!found)
                    {
                        ////////////Console.WriteLine(DaysToMonth366[i]);
                        if (months[i] > t)
                        {
                            m = i - 1;
                            found = true;
                            ////////////Console.WriteLine("366");
                            d = t - months[m] + 1;
                        }
                        else
                        {
                            i++;
                        }
                    }

                    return new int[] { year, m + 1, d };
                }
            }
        }


        internal int DayOfWeekInt()
        {
            throw new NotImplementedException();
        }

        internal static DateTime GregChineseNewYear(DateTime now)
        {
            System.Globalization.Calendar Chinese = new ChineseLunisolarCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 4, 1);
            int ChinaYear = Chinese.GetYear(now);
            DateTime Hanukkah = new DateTime(ChinaYear, 1, 1, new ChineseLunisolarCalendar());
            return Hanukkah;
        }

        internal static DateTime GregChineseNewYear()
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

        public static implicit operator DateTime(StarDate dt)
        {
            return dt.DateTime;
        }

        public static implicit operator string(StarDate dt)
        {
            return dt.ToString();
        }

        //public StarDate addYears(long years)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addMonths(long years)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addWeeks(long years)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addDays(long years)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addHours(long years)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addMinutes(long min)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addSeconds(long seconds)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addMilliseconds(long years)
        //{
        //    throw new NotImplementedException();
        //}

        //public StarDate addTicks(long years)
        //{
        //    throw new NotImplementedException();
        //}

        //public int CompareTo(object obj)
        //{
        //    throw new NotImplementedException();
        //}

        //public string ToString(string format, IFormatProvider formatProvider)
        //{
        //    throw new NotImplementedException();
        //}

        //public bool Equals([AllowNull] DateTime other)
        //{
        //    throw new NotImplementedException();
        //}

        //public int CompareTo([AllowNull] DateTime other)
        //{
        //    throw new NotImplementedException();
        //}

        //public void GetObjectData(SerializationInfo info, StreamingContext context)
        //{
        //    throw new NotImplementedException();
        //}

        //public TypeCode GetTypeCode()
        //{
        //    throw new NotImplementedException();
        //}

        public bool ToBoolean(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public byte ToByte(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public char ToChar(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public DateTime ToDateTime(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public decimal ToDecimal(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public double ToDouble(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public short ToInt16(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public int ToInt32(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public long ToInt64(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public sbyte ToSByte(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public float ToSingle(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public string ToString(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public object ToType(Type conversionType, IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public ushort ToUInt16(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public uint ToUInt32(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        public ulong ToUInt64(IFormatProvider provider)
        {
            throw new NotImplementedException();
        }

        // Constructs a StarDate from a tick count. The _ticks
        // argument specifies the date as the number of 100-nanosecond intervals
        // that have elapsed since 1/1/0001 12:00am.
        //
        public StarDate(BigInteger ticks)
        {
            //if (ticks < MinTicks || ticks > MaxTicks)
            //    throw new ArgumentOutOfRangeException(); //("_ticks", ); //Environment.GetResourceString("ArgumentOutOfRange_StarDateBadTicks"));
            //Contract.EndContractBlock();
            dateData = (UInt64)ticks;
            _timeZone = StarZone.Local;
            errorData = 0;
        }


        //private StarDate(BigInteger dateData)
        //{
        //    this.dateData = dateData;
        //    this._timeZone = Local;
        //    errorData = 0;
        //}

        public StarDate(BigInteger ticks, DateTimeKind kind)
        {
            throw new NotImplementedException();
        }

        //internal StarDate(BigInteger ticks, DateTimeKind kind, Boolean isAmbiguousDst)
        //{
        //    throw new NotImplementedException();
        //    if (ticks < MinTicks || ticks > MaxTicks)
        //    {
        //        throw new ArgumentOutOfRangeException(); //("_ticks", ); //Environment.GetResourceString("ArgumentOutOfRange_StarDateBadTicks"));
        //    }
        //    Contract.Requires(kind == DateTimeKind.Local, "Internal Constructor is for local times only");
        //    Contract.EndContractBlock();
        //    dateData = ((UInt64)ticks | (isAmbiguousDst ? KindLocalAmbiguousDst : KindLocal));
        //}

        // Constructs a StarDate from a given Year, month, and day. The
        // time-of-day of the resulting StarDate is always midnight.
        //

        public StarDate(int year)
        {
            StarDate dt = digitparams(year);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }

        public StarDate(int year, int month)
        {
            StarDate dt = digitparams(year, month);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }

        public StarDate(int year, int month, int day)
        {
            StarDate dt = digitparams(year, month, day);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }
        public StarDate(int year, int month, int day, int hour)
        {
            StarDate dt = digitparams(year, month, day, hour);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }
        public StarDate(int year, int month, int day, int hour, int minute)
        {
            StarDate dt = digitparams(year, month, day, hour, minute);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }
        public StarDate(int year, int month, int day, int hour, int minute, int second)
        {
            StarDate dt = digitparams(year, month, day, hour, minute, second);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }
        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond)
        {
            StarDate dt = digitparams(year, month, day, hour, minute, second, millisecond);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }

        public StarDate(int year, int month, int day, int hour, int minute, int second, int millisecond, int ticks)
        {
            StarDate dt = digitparams(year, month, day, hour, minute, second, millisecond, ticks);
            dateData = dt.dateData;
            errorData = dt.errorData;
            _timeZone = dt.TimeZone;
        }

        public StarDate(BigInteger ticks, BigInteger error, StarZone zone)
        {
            dateData = ticks;
            errorData = error;
            _timeZone = zone;
        }

        internal BigInteger InternalTicks
        {
            get
            {
                return dateData;
            }
        }

        internal BigInteger AdjustedTicks
        {
            get
            {
                return InternalTicks + offset.Ticks;
            }
        }

        private BigInteger InternalKind
        {
            get
            {
                return (dateData & FlagsMask);
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

        private StarDate AddTicks(BigInteger ticks)
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
            BigInteger ticks = InternalTicks;
            //if (value > MaxTicks - ticks || value < MinTicks - ticks)
            //{
            //    throw new ArgumentOutOfRangeException(); //("value", ); //Environment.GetResourceString("ArgumentOutOfRange_DateArithmetic"));
            //}
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
            if (value < -10000 || value > 10000) throw new ArgumentOutOfRangeException(); //("years", ); //Environment.GetResourceString("ArgumentOutOfRange_StarDateBadYears"));
            Contract.EndContractBlock();
            return AddMonths(value * 12);
        }

        // Compares two StarDate values, returning an integer that indicates
        // their relationship.
        //
        public static int Compare(StarDate t1, StarDate t2)
        {
            BigInteger ticks1 = t1.InternalTicks;
            BigInteger ticks2 = t2.InternalTicks;
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

            BigInteger valueTicks = ((StarDate)value).InternalTicks;
            BigInteger ticks = InternalTicks;
            if (ticks > valueTicks) return 1;
            if (ticks < valueTicks) return -1;
            return 0;
        }

        public int CompareTo(StarDate value)
        {
            BigInteger valueTicks = value.InternalTicks;
            BigInteger ticks = InternalTicks;
            if (ticks > valueTicks) return 1;
            if (ticks < valueTicks) return -1;
            return 0;
        }

        // Returns the tick count corresponding to the given Year, month, and day.
        // Will check the if the parameters are valid.
        private static long DateToTicks(int year, int month, int day)
        {
            if (year >= 1 && year <= 9999 && month >= 1 && month <= 12)
            {
                int[] days = IsLeapYear(year) ? DaysToMonth366 : DaysToMonth365;
                if (day >= 1 && day <= days[month] - days[month - 1])
                {
                    int y = year - 1;
                    int n = y * 365 + y / 4 - y / 100 + y / 400 + days[month - 1] + day - 1;
                    return n * TicksPerDay;
                }
            }
            throw new ArgumentOutOfRangeException(); //(null, ); //Environment.GetResourceString("ArgumentOutOfRange_BadYearMonthDay"));
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

        // Returns the number of days in the month given by the Year and
        // month arguments.
        //
        public static int DaysInMonth(int year, int month)
        {
            if (month < 1 || month > 12) throw new ArgumentOutOfRangeException(); //("month", ); //Environment.GetResourceString("ArgumentOutOfRange_Month"));
            Contract.EndContractBlock();
            // IsLeapYear checks the Year argument
            int[] days = IsLeapYear(year) ? DaysToMonth366 : DaysToMonth365;
            return days[month] - days[month - 1];
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
                return InternalTicks == ((StarDate)value).InternalTicks;
            }
            return false;
        }

        public bool Equals(StarDate value)
        {
            return InternalTicks == value.InternalTicks;
        }

        // Compares two StarDate values for equality. Returns true if
        // the two StarDate values are equal, or false if they are
        // not equal.
        //
        public static bool Equals(StarDate t1, StarDate t2)
        {
            return t1.InternalTicks == t2.InternalTicks;
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
        public static StarDate FromFileTime(long fileTime)
        {
            return FromFileTimeUtc(fileTime).ToLocalTime();
        }

        public static StarDate FromFileTimeUtc(long fileTime)
        {
            return new StarDate(DateTime.FromFileTimeUtc(fileTime));
        }

        // Creates a StarDate from an OLE Automation Date.
        //
        public static StarDate FromOADate(double d)
        {
            return new StarDate(DoubleDateToTicks(d), UTC);
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

        //public static StarDate SpecifyKind(StarDate value, DateTimeKind kind)
        //{
        //    return new StarDate(value.InternalTicks, kind);
        //}

        public Int64 ToBinary()
        {
            return DateTime.ToBinary();
        }

        // Return the underlying data, without adjust local times to the right time zone. Needed if performance
        // or compatability are important.
        internal Int64 ToBinaryRaw()
        {
            return (Int64)dateData;
        }

        // Returns the date part of this StarDate. The resulting value
        // corresponds to this StarDate with the time-of-day part set to
        // zero (midnight).
        //
        public StarDate Date
        {
            get
            {
                BigInteger ticks = InternalTicks;
                return new StarDate((UInt64)(ticks - ticks % TicksPerDay) | InternalKind);
            }
        }



        public int Day
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1);
                Contract.Ensures(Contract.Result<int>() <= 28);
                return GetDatePart(DatePartDay);
            }
            internal set
            {
                int diff = value - this.Day;
                this.atomic += diff * StarDate.DayTime;
            }
        }

        // Returns the day-of-week part of this StarDate. The returned value
        // is an integer between 0 and 6, where 0 indicates Sunday, 1 indicates
        // Monday, 2 indicates Tuesday, 3 indicates Wednesday, 4 indicates
        // Thursday, 5 indicates Friday, and 6 indicates Saturday.
        //
        public DayOfWeek DayOfWeek
        {
            get
            {
                Contract.Ensures(Contract.Result<DayOfWeek>() >= DayOfWeek.Sunday);
                Contract.Ensures(Contract.Result<DayOfWeek>() <= DayOfWeek.Saturday);
                return (DayOfWeek)(GetDatePart(DatePartDayOfWeek));
            }
        }

        // Returns the day-of-Year part of this StarDate. The returned value
        // is an integer between 1 and 366.
        //
        public int DayOfYear
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1);
                Contract.Ensures(Contract.Result<int>() <= 378);  // leap Year
                return GetDatePart(DatePartDayOfYear);
            }
            internal set
            {
                int diff = value - this.DayOfYear;
                this.atomic += diff * StarDate.DayTime;
            }
        }



        // Returns the hash code for this StarDate.
        //
        public override int GetHashCode()
        {
            BigInteger ticks = InternalTicks;
            return unchecked((int)ticks) ^ (int)(ticks >> 32);
        }

        // Returns the hour part of this StarDate. The returned value is an
        // integer between 0 and 23.
        //
        //public int Hour
        //{
        //    get
        //    {
        //        Contract.Ensures(Contract.Result<int>() >= 0);
        //        Contract.Ensures(Contract.Result<int>() < 24);
        //        return (int)((InternalTicks / TicksPerHour) % 24);
        //    }
        //}

        internal Boolean IsAmbiguousDaylightSavingTime()
        {
            return (InternalKind == KindLocalAmbiguousDst);
        }

        //[Pure]
        //public DateTimeKind Kind
        //{
        //    get
        //    {
        //        switch (InternalKind)
        //        {
        //            case KindUnspecified:
        //                return DateTimeKind.Unspecified;
        //            case KindUtc:
        //                return DateTimeKind.Utc;
        //            default:
        //                return DateTimeKind.Local;
        //        }
        //    }
        //}

        // Returns the millisecond part of this StarDate. The returned value
        // is an integer between 0 and 999.
        //


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
                this.atomic += diff * StarDate.MinuteTime;
            }
        }

        // Returns the month part of this StarDate. The returned value is an
        // integer between 1 and 12.
        //
        public int Month
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 1);
                return GetDatePart(DatePartMonth);
            }
            internal set
            {
                int diff = value - this.Month;
                this.atomic += diff * StarDate.month;
            }
        }

        // Returns a StarDate representing the current date and time. The
        // resolution of the returned value depends on the system timer. For
        // Windows NT 3.5 and later the timer resolution is approximately 10ms,
        // for Windows NT 3.1 it is approximately 16ms, and for Windows 95 and 98
        // it is approximately 55ms.
        //
        //        public static StarDate Now
        //        {
        //            get
        //            {
        //                Contract.Ensures(Contract.Result<StarDate>().Kind == DateTimeKind.Local);

        //                StarDate utc = UtcNow;
        //                Boolean isAmbiguousLocalDst = false;
        //                Int64 offset = TimeZoneInfo.GetStarDateNowUtcOffsetFromUtc(utc, out isAmbiguousLocalDst).Ticks;
        //                long tick = utc.Ticks + offset;
        //                if (tick > StarDate.MaxTicks)
        //                {
        //                    return new StarDate(StarDate.MaxTicks, DateTimeKind.Local);
        //                }
        //                if (tick < StarDate.MinTicks)
        //                {
        //                    return new StarDate(StarDate.MinTicks, DateTimeKind.Local);
        //                }
        //                return new StarDate(tick, DateTimeKind.Local, isAmbiguousLocalDst);
        //            }
        //        }

        //        public static StarDate UtcNow
        //        {
        //            [System.Security.SecuritySafeCritical]  // auto-generated
        //            get
        //            {
        //                Contract.Ensures(Contract.Result<StarDate>().Kind == DateTimeKind.Utc);
        //                // following code is tuned for speed. Don't change it without running benchmark.
        //                BigInteger ticks = 0;

        //                if (s_isLeapSecondsSupportedSystem)
        //                {
        //                    FullSystemTime time = new FullSystemTime();
        //                    GetSystemTimeWithLeapSecondsHandling(ref time);
        //                    return CreateStarDateFromSystemTime(ref time);
        //                }

        //                ticks = GetSystemTimeAsFileTime();

        //#if FEATURE_LEGACYNETCF
        //            // Windows Phone 7.0/7.1 return the ticks up to millisecond, not up to the 100th nanosecond.
        //            if (CompatibilitySwitches.IsAppEarlierThanWindowsPhone8)
        //            {
        //                BigInteger ticksms = ticks / TicksPerMillisecond;
        //                ticks = ticksms * TicksPerMillisecond;
        //            }
        //#endif
        //                return new StarDate(((UInt64)(ticks + FileTimeOffset)) | KindUtc);
        //            }
        //        }

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

        //[System.Security.SecuritySafeCritical]
        //internal static bool IsValidTimeWithLeapSeconds(int Year, int month, int day, int hour, int minute, int second, DateTimeKind kind)
        //{
        //    StarDate dt = new StarDate(Year, month, day);
        //    FullSystemTime time = new FullSystemTime(Year, month, dt.DayOfWeek, day, hour, minute, second);

        //    switch (kind)
        //    {
        //        case DateTimeKind.Local: return ValidateSystemTime(ref time, localTime: true);
        //        case DateTimeKind.Utc: return ValidateSystemTime(ref time, localTime: false);
        //        default:
        //            return ValidateSystemTime(ref time, localTime: true) || ValidateSystemTime(ref time, localTime: false);
        //    }
        //}

        // Returns the second part of this StarDate. The returned value is
        // an integer between 0 and 59.
        //
        public int Second
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 0);
                Contract.Ensures(Contract.Result<int>() < 60);
                return (int)((InternalTicks / TicksPerSecond) % 60);
            }
            internal set
            {
                int diff = value - this.Second;
                this.atomic += diff * StarDate.SecondTime;
            }
        }

        // Returns the tick count for this StarDate. The returned value is
        // the number of 100-nanosecond intervals that have elapsed since 1/1/0001
        // 12:00am.
        //
        public BigInteger Ticks
        {
            get
            {
                return InternalTicks;
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
                return new Time(InternalTicks % TicksPerDay);
            }
            internal set
            {
                Time diff = value - this.TimeOfDay;
                this.atomic += diff;
            }
        }

        // Returns a StarDate representing the current date. The date part
        // of the returned value is the current date, and the time-of-day part of
        // the returned value is zero (midnight).
        //
        public static StarDate Today
        {
            get
            {
                return StarDate.Now.Date;
            }
        }

        // Returns the Year part of this StarDate. The returned value is an
        // integer between 1 and 9999.
        //
        //public int Year
        //{
        //    get
        //    {
        //        Contract.Ensures(Contract.Result<int>() >= 1 && Contract.Result<int>() <= 9999);
        //        return GetDatePart(DatePartYear);
        //    }
        //}

        public static StarZone Local
        {
            get
            {
                return StarZone.Local;
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

        public StarCulture English
        {
            get
            {
                return StarCulture.InvariantCulture;
            }
        }

        public StarCulture InvariantCulture
        {
            get
            {
                return StarCulture.InvariantCulture;
            }
        }

        public Time atomic
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

        //public ulong InternalKind { get => internalKind; private set => internalKind = value; }
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

        public StarDate ChristNet
        {
            get
            {
                return ADStart;
            }
        }

        public static StarDate Manu
        {
            get
            {
                return StarDate.manu;
            }
        }

        public static string[] AllFormats
        {
            get
            {
                List<string> a = new List<string>();
                a.Add(("MM/dd/yyyy")); // ////////Console.WriteLine(aDate.ToString("MM/dd/yyyy")); // ////////Console.WriteLine(bDate.ToString("MM/dd/yyyy")); //
                a.Add(("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy")); //
                a.Add(("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy")); //
                a.Add(("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy")); //
                a.Add(("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy")); //
                a.Add(("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); // ////////Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy")); //
                a.Add(("dddd, dd MMMM yyyy HH:mm:ss")); // ////////Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy HH:mm:ss")); // ////////Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy HH:mm:ss")); //
                a.Add(("MM/dd/yyyy HH:mm")); // ////////Console.WriteLine(aDate.ToString("MM/dd/yyyy HH:mm")); // ////////Console.WriteLine(bDate.ToString("MM/dd/yyyy HH:mm")); //
                a.Add(("MM/dd/yyyy hh:mm tt")); // ////////Console.WriteLine(aDate.ToString("MM/dd/yyyy hh:mm tt")); // ////////Console.WriteLine(bDate.ToString("MM/dd/yyyy hh:mm tt")); //
                a.Add(("MM/dd/yyyy H:mm")); // ////////Console.WriteLine(aDate.ToString("MM/dd/yyyy H:mm")); // ////////Console.WriteLine(bDate.ToString("MM/dd/yyyy H:mm")); //
                a.Add(("MM/dd/yyyy h:mm tt")); // ////////Console.WriteLine(aDate.ToString("MM/dd/yyyy h:mm tt")); // ////////Console.WriteLine(bDate.ToString("MM/dd/yyyy h:mm tt")); //
                a.Add(("MM/dd/yyyy HH:mm:ss")); // ////////Console.WriteLine(aDate.ToString("MM/dd/yyyy HH:mm:ss")); // ////////Console.WriteLine(bDate.ToString("MM/dd/yyyy HH:mm:ss")); //
                a.Add(("MMMM dd")); // ////////Console.WriteLine(aDate.ToString("MMMM dd")); // ////////Console.WriteLine(bDate.ToString("MMMM dd")); //
                a.Add(("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss.fffffffK")); // ////////Console.WriteLine(aDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss.fffffffK")); // ////////Console.WriteLine(bDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss.fffffffK")); //
                a.Add(("ddd, dd MMM yyy HH’:’mm’:’ss ‘GMT’")); // ////////Console.WriteLine(aDate.ToString("ddd, dd MMM yyy HH’:’mm’:’ss ‘GMT’")); // ////////Console.WriteLine(bDate.ToString("ddd, dd MMM yyy HH’:’mm’:’ss ‘GMT’")); //
                a.Add(("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss")); // ////////Console.WriteLine(aDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss")); // ////////Console.WriteLine(bDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss")); //
                a.Add(("HH:mm")); // ////////Console.WriteLine(aDate.ToString("HH:mm")); // ////////Console.WriteLine(bDate.ToString("HH:mm")); //
                a.Add(("hh:mm tt")); // ////////Console.WriteLine(aDate.ToString("hh:mm tt")); // ////////Console.WriteLine(bDate.ToString("hh:mm tt")); //
                a.Add(("H:mm")); // ////////Console.WriteLine(aDate.ToString("H:mm")); // ////////Console.WriteLine(bDate.ToString("H:mm")); //
                a.Add(("h:mm tt")); // ////////Console.WriteLine(aDate.ToString("h:mm tt")); // ////////Console.WriteLine(bDate.ToString("h:mm tt")); //
                a.Add(("HH:mm:ss")); // ////////Console.WriteLine(aDate.ToString("HH:mm:ss")); // ////////Console.WriteLine(bDate.ToString("HH:mm:ss")); //
                a.Add(("yyyy MMMM")); // ////////Console.WriteLine(aDate.ToString("yyyy MMMM")); // ////////Console.WriteLine(bDate.ToString("yyyy MMMM")); //
                string[] vs = new string[a.Count];
                int i = 0;
                while (i < vs.Length)
                {
                    vs[i] = a[i];
                    i++;
                }
                return vs;
            }
        }

        public int Julian
        {
            get
            {
                return (this - StarDate.julian) / StarDate.DayTime;
            }

            set
            {
                int diff = value - this.Julian;
                this += diff * StarDate.DayTime;
            }
        }

        public static string DefaultFormat
        {
            get
            {
                return defaultFormat;
            }

            private set
            {
                defaultFormat = value;
            }
        }

        public int ExtraTicks
        {
            get
            {
                Contract.Ensures(Contract.Result<int>() >= 0);
                Contract.Ensures(Contract.Result<int>() < 10000);
                return (int)((AdjustedTicks % 10000));
            }
            internal set
            {
                int diff = value - this.ExtraTicks;
                this.dateData += diff;
            }
        }

        public static StarDate Maya { get => maya; internal set => maya1 = value; }
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

        public static List<StarDate> TestYear()
        {
            List<StarDate> stars = new List<StarDate>();
            StarDate dt = StarDate.maya - StarDate.week * 54;
            while (dt < StarDate.maya)
            {
                stars.Add(dt);
                dt += StarDate.DayTime;
            }
            return stars;
        }

        // Checks whether a given Year is a leap Year. This method returns true if
        // Year is a leap Year, or false if not.
        //
        public static bool IsLeapYear(int year)
        {
            if (year < 1 || year > 9999)
            {
                throw new ArgumentOutOfRangeException(); //("Year", ); //Environment.GetResourceString("ArgumentOutOfRange_Year"));
            }
            Contract.EndContractBlock();
            return year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
        }

        // Constructs a StarDate from a string. The string must specify a
        // date and optionally a time in a culture-specific or universal format.
        // Leading and trailing whitespace characters are allowed.
        //
        //public static StarDate Parse(String s)
        //{
        //    return (StarDateParse.Parse(s, StarCulture.CurrentCulture, StarDateStyles.None));
        //}

        //// Constructs a StarDate from a string. The string must specify a
        //// date and optionally a time in a culture-specific or universal format.
        //// Leading and trailing whitespace characters are allowed.
        ////
        //public static StarDate Parse(String s, IFormatProvider provider)
        //{
        //    return (StarDateParse.Parse(s, StarCulture.GetInstance(provider), StarDateStyles.None));
        //}

        //public static StarDate Parse(String s, IFormatProvider provider, StarDateStyles styles)
        //{
        //    StarCulture.ValidateStyles(styles, "styles");
        //    return (StarDateParse.Parse(s, StarCulture.GetInstance(provider), styles));
        //}

        //// Constructs a StarDate from a string. The string must specify a
        //// date and optionally a time in a culture-specific or universal format.
        //// Leading and trailing whitespace characters are allowed.
        ////
        //public static StarDate ParseExact(String s, String format, IFormatProvider provider)
        //{
        //    return (StarDateParse.ParseExact(s, format, StarCulture.GetInstance(provider), StarDateStyles.None));
        //}

        //// Constructs a StarDate from a string. The string must specify a
        //// date and optionally a time in a culture-specific or universal format.
        //// Leading and trailing whitespace characters are allowed.
        ////
        //public static StarDate ParseExact(String s, String format, IFormatProvider provider, StarDateStyles style)
        //{
        //    StarCulture.ValidateStyles(style, "style");
        //    return (StarDateParse.ParseExact(s, format, StarCulture.GetInstance(provider), style));
        //}

        //public static StarDate ParseExact(String s, String[] formats, IFormatProvider provider, StarDateStyles style)
        //{
        //    StarCulture.ValidateStyles(style, "style");
        //    return StarDateParse.ParseExactMultiple(s, formats, StarCulture.GetInstance(provider), style);
        //}

        public Time Subtract(StarDate value)
        {
            return new Time(InternalTicks - value.InternalTicks);
        }

        public Time Subtract(DateTime value)
        {
            return new Time(InternalTicks - value.Ticks);
        }

        public StarDate Subtract(TimeSpan value)
        {
            return Subtract(new Time(value));
        }

        public StarDate Subtract(Time value)
        {
            BigInteger ticks = InternalTicks;
            BigInteger valueTicks = value.Ticks;
            if (ticks - MinTicks < valueTicks || ticks - MaxTicks > valueTicks)
            {
                throw new ArgumentOutOfRangeException(); //("value", ); //Environment.GetResourceString("ArgumentOutOfRange_DateArithmetic"));
            }
            return new StarDate((UInt64)(ticks - valueTicks) | InternalKind);
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
            return TicksToOADate((long)(InternalTicks - ADStart.Ticks));
        }

        public long ToFileTime()
        {
            // Treats the input as local if it is not specified
            return ToUniversalTime().ToFileTimeUtc();
        }

        public long ToFileTimeUtc()
        {
            // Treats the input as universal if it is not specified
            //BigInteger ticks = ((InternalKind & LocalMask) != 0) ? ToUniversalTime().InternalTicks : this.InternalTicks;

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

        private StarDate ToZone(StarZone zone)
        {
            StarDate dt = this;
            dt.TimeZone = zone;
            return dt;
        }

        public String ToLongDateString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            ////////////Console.WriteLine(sdfi.CultureName);
            return StarDateFormat.Format(this, "D", StarCulture.CurrentCulture);
        }

        public String ToLongTimeString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            ////////////Console.WriteLine(sdfi.CultureName);
            return StarDateFormat.Format(this, "T", StarCulture.CurrentCulture);
        }

        public String ToShortDateString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            ////////////Console.WriteLine(sdfi.CultureName);
            return StarDateFormat.Format(this, "d", StarCulture.CurrentCulture);
        }

        public String ToShortTimeString()
        {
            Contract.Ensures(Contract.Result<String>() != null);
            //////////Console.WriteLine(this.CultureName);
            return StarDateFormat.Format(this, "t", StarCulture.CurrentCulture);
        }

        //public override String ToString()
        //{
        //    Contract.Ensures(Contract.Result<String>() != null);
        //    return StarDateFormat.Format(this, null, StarCulture.CurrentCulture);
        //}

        //public String ToString(String format)
        //{
        //    Contract.Ensures(Contract.Result<String>() != null);
        //    return StarDateFormat.Format(this, format, StarCulture.CurrentCulture);
        //}

        //public String ToString(IFormatProvider provider)
        //{
        //    Contract.Ensures(Contract.Result<String>() != null);
        //    return StarDateFormat.Format(this, null, StarCulture.GetInstance(provider));
        //}

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
        //public static Boolean TryParse(String s, out StarDate result)
        //{
        //    return StarDateParse.TryParse(s, StarCulture.CurrentCulture, StarDateStyles.None, out result);
        //}

        //public static Boolean TryParse(String s, IFormatProvider provider, StarDateStyles styles, out StarDate result)
        //{
        //    StarCulture.ValidateStyles(styles, "styles");
        //    return StarDateParse.TryParse(s, StarCulture.GetInstance(provider), styles, out result);
        //}

        //public static Boolean TryParseExact(String s, String format, IFormatProvider provider, StarDateStyles style, out StarDate result)
        //{
        //    StarCulture.ValidateStyles(style, "style");
        //    return StarDateParse.TryParseExact(s, format, StarCulture.GetInstance(provider), style, out result);
        //}

        //public static Boolean TryParseExact(String s, String[] formats, IFormatProvider provider, StarDateStyles style, out StarDate result)
        //{
        //    StarCulture.ValidateStyles(style, "style");
        //    return StarDateParse.TryParseExactMultiple(s, formats, StarCulture.GetInstance(provider), style, out result);
        //}

        //public static StarDate operator +(StarDate d, TimeSpan t)
        //{
        //    BigInteger ticks = d.InternalTicks;
        //    BigInteger valueTicks = t._ticks;
        //    if (valueTicks > MaxTicks - ticks || valueTicks < MinTicks - ticks)
        //    {
        //        throw new ArgumentOutOfRangeException(); //("t", ); //Environment.GetResourceString("ArgumentOutOfRange_DateArithmetic"));
        //    }
        //    return new StarDate((UInt64)(ticks + valueTicks) | d.InternalKind);
        //}

        //public static StarDate operator -(StarDate d, TimeSpan t)
        //{
        //    BigInteger ticks = d.InternalTicks;
        //    BigInteger valueTicks = t.Ticks;
        //    if (ticks - MinTicks < valueTicks || ticks - MaxTicks > valueTicks)
        //    {
        //        throw new ArgumentOutOfRangeException(); //("t", ); //Environment.GetResourceString("ArgumentOutOfRange_DateArithmetic"));
        //    }
        //    return new StarDate((UInt64)(ticks - valueTicks) | d.InternalKind);
        //}

        public static Time operator -(StarDate d1, StarDate d2)
        {
            return new Time(d1.InternalTicks - d2.InternalTicks);
        }




        // Returns a string array containing all of the known date and time options for the
        // current culture.  The strings returned are properly formatted date and
        // time strings for the current instance of StarDate.
        public String[] GetStarDateFormats()
        {
            Contract.Ensures(Contract.Result<String[]>() != null);
            return (GetStarDateFormats(CultureInfo.CurrentCulture));
        }

        // Returns a string array containing all of the known date and time options for the
        // using the information provided by IFormatProvider.  The strings returned are properly formatted date and
        // time strings for the current instance of StarDate.
        public String[] GetStarDateFormats(IFormatProvider provider)
        {
            Contract.Ensures(Contract.Result<String[]>() != null);
            return (StarDateFormat.GetAllStarDates(this, StarCulture.GetInstance(provider)));
        }


        // Returns a string array containing all of the date and time options for the
        // given format format and current culture.  The strings returned are properly formatted date and
        // time strings for the current instance of StarDate.
        public String[] GetStarDateFormats(char format)
        {
            Contract.Ensures(Contract.Result<String[]>() != null);
            return (GetStarDateFormats(format, CultureInfo.CurrentCulture));
        }

        // Returns a string array containing all of the date and time options for the
        // given format format and given culture.  The strings returned are properly formatted date and
        // time strings for the current instance of StarDate.
        public String[] GetStarDateFormats(char format, IFormatProvider provider)
        {
            Contract.Ensures(Contract.Result<String[]>() != null);
            return (StarDateFormat.GetAllStarDates(this, format, StarCulture.GetInstance(provider)));
        }

        //
        // IConvertible implementation
        //

        public TypeCode GetTypeCode()
        {
            throw new NotImplementedException(); //return TypeCode.StarDate;
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

        public int CompareTo([AllowNull] DateTime other)
        {
            throw new NotImplementedException();
        }

        public bool Equals([AllowNull] DateTime other)
        {
            throw new NotImplementedException();
        }

        // Tries to construct a StarDate from a given Year, month, day, hour,
        // minute, second and millisecond.
        //
        //    internal static Boolean TryCreate(int Year, int month, int day, int hour, int minute, int second, int millisecond, out StarDate result)
        //    {
        //        result = StarDate.MinValue;
        //        if (Year < 1 || Year > 9999 || month < 1 || month > 12)
        //        {
        //            return false;
        //        }
        //        int[] days = IsLeapYear(Year) ? DaysToMonth366 : DaysToMonth365;
        //        if (day < 1 || day > days[month] - days[month - 1])
        //        {
        //            return false;
        //        }

        //        if (hour < 0 || hour >= 24 || minute < 0 || minute >= 60 || second < 0 || second > 60)
        //        {
        //            return false;
        //        }
        //        if (millisecond < 0 || millisecond >= MillisPerSecond)
        //        {
        //            return false;
        //        }

        //        if (second == 60)
        //        {
        //            if (s_isLeapSecondsSupportedSystem && IsValidTimeWithLeapSeconds(Year, month, day, hour, minute, second, DateTimeKind.Unspecified))
        //            {
        //                // if we have leap second (second = 60) then we'll need to check if it is valid time.
        //                // if it is valid, then we adjust the second to 59 so StarDate will consider this second is last second
        //                // of this minute.
        //                // if it is not valid time, we'll eventually throw.
        //                // although this is unspecified StarDate kind, we'll assume the passed time is UTC to check the leap seconds.
        //                second = 59;
        //            }
        //            else
        //            {
        //                return false;
        //            }
        //        }

        //        BigInteger ticks = DateToTicks(Year, month, day) + TimeToTicks(hour, minute, second);

        //        ticks += millisecond * TicksPerMillisecond;
        //        if (ticks < MinTicks || ticks > MaxTicks)
        //        {
        //            return false;
        //        }
        //        result = new StarDate(ticks, DateTimeKind.Unspecified);
        //        return true;
        //    }
        //}

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

        internal static StarDate digitparams(params int[] vs)
        {
            return digitparams(Local, vs);
        }

        internal static StarDate digitparams(StarZone z, params int[] vs)
        {
            StarDate dt1;
            StarDate dt2;
            foreach (int entry in vs)
            {
                ////////Console.WriteLine(entry);
            }
            switch (vs.Length)
            {
                case 1:
                    dt1 = fromdigits(z, vs[0], 0, 0, 0, 0, 0, 0, 0);
                    dt2 = fromdigits(z, vs[0] + 1, 0, 0, 0, 0, 0, 0, 0);
                    return Between(dt1, dt2);
                case 2:
                    dt1 = fromdigits(z, vs[0], vs[1], 0, 0, 0, 0, 0, 0);
                    dt2 = fromdigits(z, vs[0], vs[1] + 1, 0, 0, 0, 0, 0, 0);
                    return Between(dt1, dt2);
                case 3:
                    dt1 = fromdigits(z, vs[0], vs[1], vs[2], 0, 0, 0, 0, 0);
                    dt2 = fromdigits(z, vs[0], vs[1], vs[2] + 1, 0, 0, 0, 0, 0);
                    return Between(dt1, dt2);
                case 4:
                    dt1 = fromdigits(z, vs[0], vs[1], vs[2], vs[3], 0, 0, 0, 0);
                    dt2 = fromdigits(z, vs[0], vs[1], vs[2], vs[3] + 1, 0, 0, 0, 0);
                    return Between(dt1, dt2);
                case 5:
                    dt1 = fromdigits(z, vs[0], vs[1], vs[2], vs[3], vs[4], 0, 0, 0);
                    dt2 = fromdigits(z, vs[0], vs[1], vs[2], vs[3], vs[4] + 1, 0, 0, 0);
                    return Between(dt1, dt2);
                case 6:
                    dt1 = fromdigits(z, vs[0], vs[1], vs[2], vs[3], vs[4], vs[5], 0, 0);
                    dt2 = fromdigits(z, vs[0], vs[1], vs[2], vs[3], vs[4], vs[5] + 1, 0, 0);
                    return Between(dt1, dt2);
                case 7:
                    dt1 = fromdigits(z, vs[0], vs[1], vs[2], vs[3], vs[4], vs[5], vs[6], 0);
                    dt2 = fromdigits(z, vs[0], vs[1], vs[2], vs[3], vs[4], vs[5], vs[6] + 1, 0);
                    return Between(dt1, dt2);
                default:
                    return fromdigits(z, vs[0], vs[1], vs[2], vs[3], vs[4], vs[5], vs[6], vs[7]);
            }
        }

        public static void TestFormat(string v)
        {
            TestFormat(StarDate.Now, v);
        }

        public static void TestFormat(StarDate dt, string v)
        {
            ////////Console.WriteLine(" ");
            ////////Console.WriteLine(v);
            ////////Console.WriteLine(dt.DateTime.ToString(v));
            ////////Console.WriteLine(dt.ToString(v));
            ////////Console.WriteLine(" ");
        }

        public static void PrintAllFormats()
        {
            // ////////Console.WriteLine(aDate.ToString("yyyy MMMM")); // ////////Console.WriteLine(bDate.ToString("yyyy MMMM")); //

        }

        internal static void PrintAllFormats(StarDate dt)
        {
            foreach (string entry in AllFormats)
            {
                StarDate.TestFormat(dt, entry);
            }
        }

        internal static void FullTest()
        {
            foreach (StarDate star in StarDate.TestYear())
            {
                StarDate.PrintAllFormats(star);
            }
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

        internal static void ConsoleTest(StarDate dt, StarCulture c)
        {
            StarCulture current = StarCulture.CurrentCulture;
            StarCulture.CurrentCulture = c;
            ConsoleTest(dt);
            StarCulture.CurrentCulture = current;
        }

        internal static void ConsoleTest(StarDate dt)
        {
            string[] formats = new string[] { "", "yyyyy/M/d d", "yyyyy/M/d dd", "yyyyy/M/d ddd", "yyyyy/M/d dddd", "yyyyy/M/d D", "yyyyy/M/d DD", "yyyyy/M/d DDD", "yyyyy/M/d f", "yyyyy/M/d ff", "yyyyy/M/d fff", "yyyyy/M/d ffff", "yyyyy/M/d fffff", "yyyyy/M/d ffffff", "yyyyy/M/d fffffff", "yyyyy/M/d ffffffff", "yyyyy/M/d F", "yyyyy/M/d F", "yyyyy/M/d FF", "yyyyy/M/d FFF", "yyyyy/M/d FFFF", "yyyyy/M/d FFFFF", "yyyyy/M/d FFFFFF", "yyyyy/M/d FFFFFFF", "yyyyy/M/d g", "yyyyy/M/d gg", "yyyyy/M/d G", "yyyyy/M/d GG", "yyyyy/M/d h", "yyyyy/M/d hh", "yyyyy/M/d H", "yyyyy/M/d HH", "yyyyy/M/d K", "yyyyy/M/d m", "yyyyy/M/d mm", "yyyyy/M/d M", "yyyyy/M/d MM", "yyyyy/M/d MMM", "yyyyy/M/d MMMM", "yyyyy/M/d s", "yyyyy/M/d ss", "yyyyy/M/d t", "yyyyy/M/d tt", "yyyyy/M/d y", "yyyyy/M/d yy", "yyyyy/M/d yyy", "yyyyy/M/d yyyy", "yyyyy/M/d yyyyy", "yyyyy/M/d yyyyyyy", "yyyyy/M/d yyyyyyyy", "yyyyy/M/d yyyyyyyyyy", "yyyyy/M/d yyyyyyyyyyyy", "yyyyy/M/d yyyyyyyyyyyyy", "yyyyy/M/d z", "yyyyy/M/d zz", "yyyyy/M/d zzz", "yyyyy/M/d zzzz", "yyyyy/M/d zzzzz", "yyyyy/M/d :", "yyyyy/M/d /" };
            foreach (string format in formats)
            {
                ////Console.WriteLine(dt.ToString(format));
            }
        }

        //public StarDate(int Year, int month, int day, int hour, int minute, int second, int millisecond, StarZone z) : this(Year, month, day, hour, minute, second, millisecond)
        //{
        //    this.z = z;
        //}
    }
}