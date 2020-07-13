// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==
using StarCalendar;
using System;
using System.Collections.Generic;
using System.Diagnostics.Contracts;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;

namespace StarCalendar
{
    //using System.Text;
    //using System.Threading;
    //using System.Globalization;
    //using System.Collections.Generic;
    //using System.Runtime.CompilerServices;
    //using System.Runtime.InteropServices;
    //using System.Runtime.Versioning;
    //using System.Security;
    //using System.Diagnostics.Contracts;
    //using System;
    /* source urls
     * https://docs.oracle.com/cd/E41183_01/DR/Date_Formats.html#DALc02a_2726006080_11927
     * https://www.w3.org/QA/Tips/iso-date
     * https://www.w3schools.com/js/js_date_formats.asp
     * https://www.c-sharpcorner.com/blogs/date-and-time-format-in-c-sharp-programming1
     */

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
        "ddd"               short WeekDays StarName (abbreviation)     Mon
        "dddd"              full WeekDays StarName                     Monday
        "dddd*"             full WeekDays StarName                     Monday


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

    //This class contains only static members and does not require the serializable attribute.
    public class StarDateFormat
    {

        internal const int MaxSecondsFractionDigits = 7;
        internal static readonly Time NullOffset = new Time(0);

        internal static char[] allStandardFormats =
        {
            'd', 'D', 'f', 'F', 'g', 'G',
            'm', 'M', 'o', 'O', 'r', 'R',
            's', 't', 'T', 'u', 'U', 'y', 'Y',
        };

        internal const String RoundtripFormat = "yyyy'-'MM'-'dd'T'HH':'mm':'ss.fffffffK";
        internal const String RoundtripStarDateUnfixed = "yyyy'-'MM'-'ddTHH':'mm':'ss zzz";

        private const int DEFAULT_ALL_StarDateS_SIZE = 132;

        internal static readonly StarDateFormat InvariantFormatInfo = StarCulture.InvariantCulture.StarDateFormat;
        internal static readonly string[] InvariantAbbreviatedMonthNames = InvariantFormatInfo.AbbreviatedMonthNames;
        internal static readonly string[] InvariantAbbreviatedDayNames = InvariantFormatInfo.AbbreviatedDayNames;
        internal const string Gmt = "GMT";

        internal static String[] fixedNumberFormats = new String[] {
            "0",
            "00",
            "000",
            "0000",
            "00000",
            "000000",
            "0000000",
        };
        private string[] abbreviatedMonthNames;
        private string[] abbreviatedDayNames;
        private static object cal1;
        //private static StarDateFormat invariantInfo;

        //private Func<string[]> abbreviatedMonthNames1;
        //private Func<string[]> abbreviatedDayNames1;

        public StarDateFormat(string[] abbreviatedMonthNames1, string[] abbreviatedDayNames1)
        {
            this.abbreviatedMonthNames = abbreviatedMonthNames1;
            this.abbreviatedDayNames = abbreviatedDayNames1;
        }

        //public static StringBuilderCache StringBuilderCache { get; private set; }
        public StarDateFormat CurrentInfo { get; internal set; }
        public string[] AbbreviatedMonthNames
        {
            get
            {
                return abbreviatedMonthNames;
            }

            private set
            {
                abbreviatedMonthNames = value;
            }
        }
        public string[] AbbreviatedDayNames
        {
            get
            {
                return abbreviatedDayNames;
            }

            private set
            {
                abbreviatedDayNames = value;
            }
        }
        public static IFormatProvider InvariantInfo
        {
            get
            {
                return StarCulture.InvariantCulture.FormatProvider;
            }
        }
        //public static object StarLEnvironment { get; private set; }
        //public static DateTimeFormatInfoScanner StarDateFormatInfoScanner { get; private set; }
        public static string JapaneseEraStart { get; private set; }
        public static StarCulture Cal
        {
            get
            {
                return StarCulture.CurrentCulture;
            }

            private set
            {
                cal1 = value;
            }
        }


        internal static int ParseRepeatPattern(String format, int pos, char patternChar)
        {
            int len = format.Length;
            int index = pos + 1;
            while ((index < len) && (format[index] == patternChar))
            {
                index++;
            }
            return (index - pos);
        }

        private static String FormatDayOfWeek(int dayOfWeek, int repeat, StarCulture sdfi)
        {
            Contract.Assert(dayOfWeek >= 0 && dayOfWeek <= 6, "dayOfWeek >= 0 && dayOfWeek <= 6");
            if (repeat == 3)
            {
                return (sdfi.GetAbbreviatedDayName((DayOfWeek)dayOfWeek));
            }
            // Call sdfi.GetDayName() here, instead of accessing DayNames property, because we don't
            // want a clone of DayNames, which will hurt perf.
            return (sdfi.GetDayName((DayOfWeek)dayOfWeek));
        }

        private string GetDayName(DayOfWeek dayOfWeek)
        {
            throw new NotImplementedException();
        }

        private string GetAbbreviatedDayName(DayOfWeek dayOfWeek)
        {
            throw new NotImplementedException();
        }

        private static String FormatMonth(int month, int repeatCount, StarCulture sdfi)
        {
            Contract.Assert(month >= 1 && month <= 12, "Month >=1 && Month <= 12");
            if (repeatCount == 3)
            {
                return (sdfi.GetAbbreviatedMonthName(month));
            }
            // Call month() here, instead of accessing MonthNames property, because we don't
            // want a clone of MonthNames, which will hurt perf.
            return (sdfi.GetMonthName(month));
        }

        private string GetMonthName(int month)
        {
            throw new NotImplementedException();
        }

        private string GetAbbreviatedMonthName(int month)
        {
            throw new NotImplementedException();
        }

        internal static int ParseQuoteString(String format, int pos, StringBuilder result)
        {
            //
            // NOTE : pos will be the index of the quote character in the 'format' string.
            //
            int formatLen = format.Length;
            int beginPos = pos;
            char quoteChar = format[pos++]; // Get the character used to quote the following string.

            bool foundQuote = false;
            while (pos < formatLen)
            {
                char ch = format[pos++];
                if (ch == quoteChar)
                {
                    foundQuote = true;
                    break;
                }
                else if (ch == '\\')
                {
                    // The following are used to support escaped character.
                    // Escaped character is also supported in the quoted string.
                    // Therefore, someone can use a format like "'minute:' mm\"" to display:
                    //  minute: 45"
                    // because the second double quote is escaped.
                    if (pos < formatLen)
                    {
                        result.Append(format[pos++]);
                    }
                    else
                    {
                        //
                        // This means that '\' is at the end of the formatting string.
                        //
                        ////////////Console.WriteLine("throw new FormatException(StarLEnvironment.GetResourceString(" + " Format_InvalidString" + "));");
                        throw new NotImplementedException();
                    }
                }
                else
                {
                    result.Append(ch);
                }
            }

            if (!foundQuote)
            {
                // Local we can't find the matching quote.
                //throw new FormatException(
                //        String.Format(
                //            StarCulture.CurrentCulture,
                //            StarLEnvironment.GetResourceString("Format_BadQuote"), quoteChar));
                throw new NotImplementedException();
            }

            //
            // Return the character count including the begin/end quote characters and enclosed string.
            //
            return (pos - beginPos);
        }

        //
        // Get the next character at the index of 'pos' in the 'format' string.
        // Return value of -1 means 'pos' is already at the end of the 'format' string.
        // Otherwise, return value is the int value of the next character.
        //
        internal static int ParseNextChar(String format, int pos)
        {
            if (pos >= format.Length - 1)
            {
                return (-1);
            }
            return ((int)format[pos + 1]);
        }

        //
        //  IsUseGenitiveForm
        //
        //  Actions: Check the format to see if we should use genitive Month in the formatting.
        //      Starting at the position (index) in the (format) string, look back and look ahead to
        //      see if there is "d" or "dd".  In the case like "d MMMM" or "MMMM dd", we can use
        //      genitive form.  Genitive form is not used if there is more than two "d".
        //  Arguments:
        //      format      The format string to be scanned.
        //      index       Where we should start the scanning.  This is generally where "M" starts.
        //      tokenLen    The len of the current pattern character.  This indicates how many "M" that we have.
        //      patternToMatch  The pattern that we want to search. This generally uses "d"
        //
        private static bool IsUseGenitiveForm(String format, int index, int tokenLen, char patternToMatch)
        {
            int i;
            int repeat = 0;
            //
            // Look back to see if we can find "d" or "ddd"
            //

            // Find first "d".
            for (i = index - 1; i >= 0 && format[i] != patternToMatch; i--) {  /*Do nothing here */ };

            if (i >= 0)
            {
                // Find a "d", so look back to see how many "d" that we can find.
                while (--i >= 0 && format[i] == patternToMatch)
                {
                    repeat++;
                }
                //
                // repeat == 0 means that we have one (patternToMatch)
                // repeat == 1 means that we have two (patternToMatch)
                //
                if (repeat <= 1)
                {
                    return (true);
                }
                // Note that we can't just stop here.  We may find "ddd" while looking back, and we have to look
                // ahead to see if there is "d" or "dd".
            }

            //
            // If we can't find "d" or "dd" by looking back, try look ahead.
            //

            // Find first "d"
            for (i = index + tokenLen; i < format.Length && format[i] != patternToMatch; i++) { /* Do nothing here */ };

            if (i < format.Length)
            {
                repeat = 0;
                // Find a "d", so contine the walk to see how may "d" that we can find.
                while (++i < format.Length && format[i] == patternToMatch)
                {
                    repeat++;
                }
                //
                // repeat == 0 means that we have one (patternToMatch)
                // repeat == 1 means that we have two (patternToMatch)
                //
                if (repeat <= 1)
                {
                    return (true);
                }
            }
            return (false);
        }


        //
        //  FormatCustomized
        //
        //  Actions: Format the StarDate instance using the specified format.
        //
        internal static String FormatCustomized(StarDate StarDate, String format, StarCulture sdfi, Time offset)
        {
            StringBuilder result = new StringBuilder();
            int i = 0;
            int tokenLen, hour12;

            while (i < format.Length)
            {
                char ch = format[i];
                int nextChar;
                switch (ch)
                {
                    case 'b':
                    case 'B':
                        ////////Console.WriteLine("Writing Millions to Quadrillions of Years");
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        result.Append(StarDate.billion);
                        break;
                    case 'g':
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        result.Append(StarCulture.CurrentCulture.GetEraName(StarDate));
                        break;
                    case 'h':
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        hour12 = StarDate.Hour % 12;
                        if (hour12 == 0)
                        {
                            hour12 = 12;
                        }
                        FormatDigits(result, hour12, tokenLen);
                        break;
                    case 'H':
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        FormatDigits(result, StarDate.Hour, tokenLen);
                        break;
                    case 'm':
                        tokenLen = ParseRepeatPattern(format, i, ch); //throw new NotImplementedException();
                        FormatDigits(result, StarDate.Minute, tokenLen);
                        break;
                    case 's':
                        tokenLen = ParseRepeatPattern(format, i, ch); //throw new NotImplementedException();
                        FormatDigits(result, StarDate.Second, tokenLen);
                        break;
                    case 'f':
                    case 'F':
                        tokenLen = ParseRepeatPattern(format, i, ch);

                        if (tokenLen <= MaxSecondsFractionDigits)
                        {
                            long fraction = (long)(StarDate.Ticks % StarDate.TicksPerSecond);
                            fraction = fraction / (long)Math.Pow(10, 7 - tokenLen);
                            if (ch == 'f')
                            {
                                result.Append(((int)fraction).ToString(fixedNumberFormats[tokenLen - 1], StarCulture.InvariantCulture.FormatProvider));
                            }
                            else
                            {
                                int effectiveDigits = tokenLen;
                                while (effectiveDigits > 0)
                                {
                                    if (fraction % 10 == 0)
                                    {
                                        fraction = fraction / 10;
                                        effectiveDigits--;
                                    }
                                    else
                                    {
                                        break;
                                    }
                                }
                                if (effectiveDigits > 0)
                                {
                                    result.Append(((int)fraction).ToString(fixedNumberFormats[effectiveDigits - 1], StarCulture.InvariantCulture.FormatProvider));
                                }
                                else
                                {
                                    // No fraction to emit, so see if we should remove decimal also.
                                    if (result.Length > 0 && result[result.Length - 1] == '.')
                                    {
                                        result.Remove(result.Length - 1, 1);
                                    }
                                }
                            }
                        }
                        else
                        {
                            throw new NotImplementedException();
                            //throw new FormatException(StarLEnvironment.GetResourceString("Format_InvalidString"));
                        }
                        break;
                    case 't':
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        if (tokenLen == 1)
                        {
                            if (StarDate.Hour < 12)
                            {
                                if (sdfi.AMDesignator.Length >= 1)
                                {
                                    result.Append(sdfi.AMDesignator[0]);
                                }
                            }
                            else
                            {
                                if (sdfi.PMDesignator.Length >= 1)
                                {
                                    result.Append(sdfi.PMDesignator[0]);
                                }
                            }

                        }
                        else
                        {
                            result.Append((StarDate.Hour < 12 ? sdfi.AMDesignator : sdfi.PMDesignator));
                        }
                        ////////Console.WriteLine(result);
                        //throw new NotImplementedException();
                        break;
                    case 'D':
                        //
                        // tokenLen == 1 : Two letter Day of Week
                        // tokenLen == 2 : Day of week as a three-leter abbreviation.
                        // tokenLen == 3 : Day of week as its full StarName.
                        //
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        switch (tokenLen)
                        {
                            case 1:
                                result.Append(StarCulture.CurrentCulture.GetSuperShortDayName(StarDate.DayOfWeek));
                                break;
                            case 2:
                                result.Append(StarCulture.CurrentCulture.GetShortDayName(StarDate.DayOfWeek));
                                break;
                            case 3:
                            default:
                                //Console.WriteLine(StarDate.DayOfWeek);
                                StarCulture.CurrentCulture.WriteAllWeekDays();
                                result.Append(StarCulture.CurrentCulture.GetDayName(StarDate.DayOfWeek));
                                break;
                        }
                        ////Console.WriteLine(result);
                        break;
                    case 'd':
                        //
                        // tokenLen == 1 : Day of Month as digits with no leading zero.
                        // tokenLen == 2 : Day of Month as digits with leading zero for single-digit months.
                        // tokenLen == 3 : Day of Month as ordinal abbreviation i.e. 1st
                        // tokenLen >= 4 : Day of Month as ordinal word i.e. First
                        //
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        switch (tokenLen)
                        {
                            case 1:
                                result.Append(StarDate.Day);
                                break;
                            case 2:
                                int day = StarDate.Day;
                                if (day < 10)
                                {
                                    result.Append("0" + day);
                                }
                                else
                                {
                                    result.Append(day);
                                }
                                break;
                            case 3:
                                result.Append(StarCulture.CurrentCulture.Ordinal(StarDate.Day));
                                break;
                            case 4:
                            default:
                                result.Append(StarCulture.CurrentCulture.LongOrdinal(StarDate.Day));
                                break;
                        }
                        ////Console.WriteLine(result);
                        //throw new NotImplementedException();
                        break;
                    case 'M':
                        //
                        // tokenLen == 1 : Month as digits with no leading zero.
                        // tokenLen == 2 : Month as digits with leading zero for single-digit months.
                        // tokenLen == 3 : Month as a three-letter abbreviation.
                        // tokenLen >= 4 : Month as its full StarName.
                        //
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        int Month = StarDate.Month;
                        switch (tokenLen)
                        {
                            case 1:
                                result.Append(Month);
                                break;
                            case 2:
                                result.Append(AddZero(Month));
                                break;
                            case 3:
                                result.Append(sdfi.AbbreviatedMonthNames[Month - 1]);
                                break;
                            case 4:
                                result.Append(sdfi.MonthNames[Month - 1]);
                                break;
                            default:
                                result.Append(sdfi.MonthNames[Month - 1]);
                                break;
                        }
                        ////Console.WriteLine(result);
                        //throw new NotImplementedException();
                        break;
                    case 'y':
                        // Notes about OS behavior:
                        // y: Always print (Year % 100). No leading zero.
                        // yy: Always print (Year % 100) with leading zero.
                        // yyy/yyyy/yyyyy/... : Print Year value.  No leading zero.

                        int year = StarDate.Year; //throw new NotImplementedException();
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        ////Console.WriteLine(result);
                        ////Console.WriteLine(tokenLen);

                        switch (tokenLen)
                        {
                            case 1:
                                result.Append(year % 100);
                                break;
                            case 2:
                                year %= 100;
                                if (year.ToString(StarCulture.InvariantCulture.FormatProvider).Length == 1)
                                {
                                    result.Append(AddZero(year));
                                }
                                else
                                {
                                    result.Append(year);
                                }
                                break;
                            case 3:
                                string y = year.ToString(InvariantInfo);
                                while (y.Length < 3)
                                {
                                    y = "0" + y;
                                }
                                result.Append(y);
                                break;
                            case 4:
                            case 5: result.Append(year.ToString()); break;
                            default:
                                result.Append(StarDate.fullyear % Math.Pow(10, tokenLen));
                                break;
                        }
                        ////Console.WriteLine(result);
                        //throw new NotImplementedException();
                        break;
                    case 'z':
                    case 'K':
                        //z and k are the same in StarDate but not in 
                        tokenLen = ParseRepeatPattern(format, i, ch);
                        result.Append(StarDate.TimeZone.ToString(tokenLen, StarDate));
                        break;
                    case ':':
                        result.Append(sdfi.TimeSeparator); //throw new NotImplementedException();
                        tokenLen = 1;
                        break;
                    case '/':
                        ////////////Console.WriteLine(sdfi == null);
                        ////////////Console.WriteLine(sdfi.GetDateSeparator());
                        result.Append(sdfi.GetDateSeparator()); ////throw new NotImplementedException();
                        tokenLen = 1;
                        ////////Console.WriteLine(result);
                        break;
                    case '\'':
                    case '\"':
                        StringBuilder enquotedString = new StringBuilder(); //throw new NotImplementedException();
                        tokenLen = ParseQuoteString(format, i, enquotedString);
                        result.Append(enquotedString);
                        break;
                    case '%':
                        // Optional format character.
                        // For example, format string "%d" will print day of Month
                        // without leading zero.  Most of the cases, "%" can be ignored.
                        nextChar = ParseNextChar(format, i); //throw new NotImplementedException();
                        // nextChar will be -1 if we already reach the end of the format string.
                        // Besides, we will not allow "%%" appear in the pattern.
                        if (nextChar >= 0 && nextChar != (int)'%')
                        {
                            //////////Console.WriteLine("Append");
                            result.Append(FormatCustomized(StarDate, ((char)nextChar).ToString(), sdfi, offset));
                            tokenLen = 2;
                        }
                        else
                        {
                            //
                            // This means that '%' is at the end of the format string or
                            // "%%" appears in the format string.
                            //
                            throw new NotImplementedException();
                            //throw new FormatException(StarLEnvironment.GetResourceString("Format_InvalidString"));
                        }
                        break;
                    case '\\':
                        // Escaped character.  Can be used to insert character into the format string.
                        // For exmple, "\d" will insert the character 'd' into the string.
                        //
                        // NOTENOTE : we can remove this format character if we enforce the enforced quote
                        // character rule.
                        // That is, we ask everyone to use single quote or double quote to insert characters,
                        // then we can remove this character.
                        //
                        nextChar = ParseNextChar(format, i); //throw new NotImplementedException();
                        if (nextChar >= 0)
                        {
                            result.Append(((char)nextChar));
                            tokenLen = 2;
                        }
                        else
                        {
                            //
                            // This means that '\' is at the end of the formatting string.
                            //
                            throw new NotImplementedException();
                            //throw new FormatException(StarLEnvironment.GetResourceString("Format_InvalidString"));
                        }
                        break;
                    default:
                        // NOTENOTE : we can remove this rule if we enforce the enforced quote
                        // character rule.
                        // That is, if we ask everyone to use single quote or double quote to insert characters,
                        // then we can remove this default block.
                        result.Append(ch); //throw new NotImplementedException();
                        tokenLen = 1;
                        break;
                }
                i += tokenLen;
            }
            return StringBuilderCache.GetStringAndRelease(result);

        }

        private static void FormatDigits(StringBuilder result, int hour12, int tokenLen)
        {
            string output = hour12.ToString();
            while (output.Length < tokenLen)
            {
                output = "0" + output;
            }
            result.Append(output);
        }

        private static string AddZero(int month)
        {
            string s = month.ToString();
            if (s.Length == 1)
            {
                s = "0" + s;
            }
            return s;
        }

        //private static bool FormatHebrewMonthName(StarDate starDate, int month, int tokenLen, StarCulture sdfi)
        //{
        //    throw new NotImplementedException();
        //}

        //private static void HebrewFormatDigits(StringBuilder result, int day)
        //{
        //    ////////////Console.WriteLine("I have no idea what this does but I don't want this to run since I'm not using the Hebrew StarCulture");
        //    //throw new NotImplementedException();
        //}

        //private static void FormatDigits(StringBuilder result, int hour12, int tokenLen)
        //{
        //    ////////////Console.WriteLine("Probably Pointless Method");
        //}


        // output the 'z' famliy of formats, which output a the offset from UTC, e.g. "-07:30"
        private static void FormatCustomizedTimeZone(StarDate StarDate, Time offset, String format, Int32 tokenLen, Boolean timeOnly, StringBuilder result)
        {
            // See if the instance already has an offset
            Boolean StarDateFormat = (offset == NullOffset);
            if (StarDateFormat)
            {
                // No offset. The instance is a StarDate and the output should be the local time zone

                if (timeOnly && StarDate.GetTicks() < StarDate.TicksPerDay)
                {
                    // For time only format and a time only input, the time offset on 0001/01/01 is less
                    // accurate than the system's current offset because of daylight saving time.
                    offset = StarZone.GetLocalUtcOffset(StarDate.Now);
                }
                else if (StarDate.TimeZone == StarZone.UTC)
                {
#if FEATURE_CORECLR
                    offset = TimeSpanInfo.Zero;
#else // FEATURE_CORECLR
                    // This code path points to a bug in user code. It would make sense to return a 0 offset in this case.
                    // However, because it was only possible to detect this in Whidbey, there is user code that takes a
                    // dependency on being serialize a UTC StarDate using the 'z' format, and it will work almost all the
                    // time if it is offset by an incorrect conversion to local time when parsed. Therefore, we need to
                    // explicitly emit the local time offset, which we can do by removing the UTC flag.
                    InvalidFormatForUtc(format, StarDate);
                    //StarDate = StarDate.SpecifyKind(StarDate, StarData.Local);
                    offset = StarZone.GetLocalUtcOffset(StarDate);
#endif // FEATURE_CORECLR
                }
                else
                {
                    offset = StarZone.GetLocalUtcOffset(StarDate);
                }
            }
            if (offset >= Time.Zero)
            {
                result.Append('+');
            }
            else
            {
                result.Append('-');
                // get a positive offset, so that you don't need a separate code path for the negative numbers.
                offset = offset.Negate();
            }

            if (tokenLen <= 1)
            {
                // 'z' format e.g "-7"
                result.AppendFormat(StarCulture.InvariantCulture.GetFormat(), "{0:0}", offset.Hours);
            }
            else
            {
                // 'zz' or longer format e.g "-07"
                result.AppendFormat(StarCulture.InvariantCulture.GetFormat(), "{0:00}", offset.Hours);
                if (tokenLen >= 3)
                {
                    // 'zzz*' or longer format e.g "-07:30"
                    result.AppendFormat(StarCulture.InvariantCulture.GetFormat(), ":{0:00}", offset.Minutes);
                }
            }
        }

        // output the 'K' format, which is for round-tripping the data
        private static void FormatCustomizedRoundripTimeZone(StarDate dt, Time offset, StringBuilder result)
        {

            // The objective of this format is to round trip the data in the type
            // For StarDate it should round-trip the Kind value and preserve the time zone.
            // StarDateOffset instance, it should do so by using the internal time zone.

            if (offset == NullOffset)
            {
                // source is a date time, so behavior depends on the metadata.
                if (dt.TimeZone == StarDate.Local)
                {
                    // This should output the local offset, e.g. "-07:30"
                    offset = StarZone.GetLocalUtcOffset(dt, StarZone.NoThrowOnInvalidTime);
                    // fall through to shared time zone output code
                }
                else if (dt.TimeZone == StarZone.UTC)
                {
                    // The 'Z' constant is a marker for a UTC date
                    result.Append("Z");
                    return;
                }
                else
                {
                    // If the metadata is unspecified, we output nothing here
                    return;
                }
            }
            if (offset >= Time.Zero)
            {
                result.Append('+');
            }
            else
            {
                result.Append('-');
                // get a positive offset, so that you don't need a separate code path for the negative numbers.
                offset = offset.Negate();
            }

            result.AppendFormat(StarCulture.InvariantCulture.GetFormat(), "{0:00}:{1:00}", offset.Hours, offset.Minutes);
        }


        internal static String GetRealFormat(String format, StarCulture sdfi)
        {
            String realFormat = null;
            if (sdfi == null)
            {
                sdfi = StarCulture.CurrentCulture;
            }

            switch (format[0])
            {
                case 'd':       // Short Date
                    realFormat = sdfi.ShortDatePattern;
                    break;
                case 'D':       // Long Date
                    realFormat = sdfi.LongDatePattern;
                    break;
                case 'f':       // Full (long date + short time)
                    realFormat = sdfi.LongDatePattern + " " + sdfi.ShortTimePattern;
                    break;
                case 'F':       // Full (long date + long time)
                    realFormat = sdfi.FullStarDatePattern;
                    break;
                case 'g':       // General (short date + short time)
                    realFormat = sdfi.GeneralShortTimePattern;
                    break;
                case 'G':       // General (short date + long time)
                    realFormat = sdfi.GeneralLongTimePattern;
                    break;
                case 'm':
                case 'M':       // Month/Day Date
                    realFormat = sdfi.MonthDayPattern;
                    break;
                case 'o':
                case 'O':
                    realFormat = RoundtripFormat;
                    break;
                case 'r':
                case 'R':       // RFC 1123 Standard
                    realFormat = sdfi.RFC1123Pattern;
                    break;
                case 's':       // Sortable without Time StarZone Info
                    realFormat = sdfi.SortableStarDatePattern;
                    break;
                case 't':       // Short Time
                    realFormat = sdfi.ShortTimePattern;
                    break;
                case 'T':       // Long Time
                    realFormat = sdfi.LongTimePattern;
                    break;
                case 'u':       // Universal with Sortable format
                    realFormat = sdfi.UniversalSortableStarDatePattern;
                    break;
                case 'U':       // Universal with Full (long date + long time) format
                    realFormat = sdfi.FullStarDatePattern;
                    break;
                case 'y':
                case 'Y':       // Year/Month Date
                    realFormat = sdfi.YearMonthPattern;
                    break;
                default:
                    throw new NotImplementedException();
                    //throw new FormatException(StarLEnvironment.GetResourceString("Format_InvalidString"));
            }
            return (realFormat);
        }


        // Expand a pre-defined format string (like "D" for long date) to the real format that
        // we are going to use in the date time parsing.
        // This method also convert the StarDate if necessary (e.g. when the format is in Universal time),
        // and change sdfi if necessary (e.g. when the format should use invariant culture).
        //
        private static String ExpandPredefinedFormat(String format, ref StarDate StarDate, ref StarCulture sdfi, ref Time offset)
        {
            switch (format[0])
            {
                case 's':       // Sortable without Time StarZone Info
                    sdfi = StarCulture.InvariantCulture;
                    break;
                case 'u':       // Universal time in sortable format.
                    if (offset != NullOffset)
                    {
                        // DateTime to UTC invariants mean this will be in range
                        StarDate = StarDate - offset;
                    }
                    else if (StarDate.TimeZone == StarDate.Local)
                    {

                        InvalidFormatForLocal(format, StarDate);
                    }
                    sdfi = StarCulture.InvariantCulture;
                    break;
            }
            format = GetRealFormat(format, sdfi);
            return (format);
        }

        //private static string GetRealFormat(string format, StarCulture sdfi)
        //{
        //    throw new NotImplementedException();
        //}

        internal static String Format(StarDate StarDate, String format, StarCulture sdfi)
        {
            //////////////Console.WriteLine(format);
            //throw new NotImplementedException();
            ////////////Console.WriteLine(sdfi.CultureName);
            return Format(StarDate, format, sdfi, NullOffset);
        }


        internal static String Format(StarDate StarDate, String format, StarCulture sdfi, Time offset)
        {
            Contract.Requires(sdfi != null);

            if (format.Length == 1)
            {
                switch (format[0])
                {
                    case 'O':
                    case 'o':
                        return StringBuilderCache.GetStringAndRelease(FastFormatRoundtrip(StarDate, offset));
                    case 'R':
                    case 'r':
                        return StringBuilderCache.GetStringAndRelease(FastFormatRfc1123(StarDate, offset, sdfi));
                }

                format = ExpandPredefinedFormat(format, ref StarDate, ref sdfi, ref offset);
            }
            ////////////Console.WriteLine(sdfi.CultureName);
            ////////////Console.WriteLine("Return");
            return FormatCustomized(StarDate, format, sdfi, offset);
        }

        internal static StringBuilder FastFormatRfc1123(StarDate StarDate, Time offset, StarCulture sdfi)
        {
            // ddd, dd MMM yyyy HH:mm:ss GMT
            const int Rfc1123FormatLength = 29;
            StringBuilder result = StringBuilderCache.Acquire(Rfc1123FormatLength);

            if (offset != NullOffset)
            {
                // DateTime to UTC invariants
                StarDate = StarDate - offset;
            }

            int year, month, day;
            StarDate.GetDatePart(out year, out month, out day);

            result.Append(InvariantAbbreviatedDayNames[StarDate.DayOfWeekInt()]);
            result.Append(',');
            result.Append(' ');
            AppendNumber(result, day, 2);
            result.Append(' ');
            result.Append(InvariantAbbreviatedMonthNames[month - 1]);
            result.Append(' ');
            AppendNumber(result, year, 4);
            result.Append(' ');
            AppendHHmmssTimeOfDay(result, StarDate);
            result.Append(' ');
            result.Append(Gmt);

            return result;
        }

        internal static StringBuilder FastFormatRoundtrip(StarDate StarDate, Time offset)
        {
            // yyyy-MM-ddTHH:mm:ss.fffffffK
            const int roundTripFormatLength = 28;
            StringBuilder result = StringBuilderCache.Acquire(roundTripFormatLength);

            int year, month, day;
            StarDate.GetDatePart(out year, out month, out day);

            AppendNumber(result, year, 4);
            result.Append('-');
            AppendNumber(result, month, 2);
            result.Append('-');
            AppendNumber(result, day, 2);
            result.Append('T');
            AppendHHmmssTimeOfDay(result, StarDate);
            result.Append('.');

            BigInteger fraction = StarDate.GetTicks() % StarDate.TicksPerSecond;
            AppendNumber(result, fraction, 7);

            FormatCustomizedRoundripTimeZone(StarDate, offset, result);

            return result;
        }

        private static void AppendNumber(StringBuilder result, BigInteger fraction, int v)
        {
            throw new NotImplementedException();
        }

        private static void AppendHHmmssTimeOfDay(StringBuilder result, StarDate StarDate)
        {
            // HH:mm:ss
            AppendNumber(result, StarDate.Hour, 2);
            result.Append(':');
            AppendNumber(result, StarDate.Minute, 2);
            result.Append(':');
            AppendNumber(result, StarDate.Second, 2);
        }

        internal static void AppendNumber(StringBuilder builder, long val, int digits)
        {
            for (int i = 0; i < digits; i++)
            {
                builder.Append('0');
            }

            int index = 1;
            while (val > 0 && index <= digits)
            {
                builder[builder.Length - index] = (char)('0' + (val % 10));
                val = val / 10;
                index++;
            }

            //BCLDebug.Assert(val == 0, "StarDateFormat.AppendNumber(): digits less than size of val");
        }

        internal static String[] GetAllStarDates(StarDate StarDate, char format, StarCulture sdfi)
        {
            Contract.Requires(sdfi != null);
            String[] allFormats = null;
            String[] results = null;

            switch (format)
            {
                case 'd':
                case 'D':
                case 'f':
                case 'F':
                case 'g':
                case 'G':
                case 'm':
                case 'M':
                case 't':
                case 'T':
                case 'y':
                case 'Y':
                    allFormats = sdfi.GetAllStarDatePatterns(format);
                    results = new String[allFormats.Length];
                    for (int i = 0; i < allFormats.Length; i++)
                    {
                        results[i] = Format(StarDate, allFormats[i], sdfi);
                    }
                    break;
                case 'U':
                    StarDate universalTime = StarDate.ToUniversalTime();
                    allFormats = sdfi.GetAllStarDatePatterns(format);
                    results = new String[allFormats.Length];
                    for (int i = 0; i < allFormats.Length; i++)
                    {
                        results[i] = Format(universalTime, allFormats[i], sdfi);
                    }
                    break;
                //
                // The following ones are special cases because these patterns are read-only in
                // StarDateFormat.
                //
                case 'r':
                case 'R':
                case 'o':
                case 'O':
                case 's':
                case 'u':
                    results = new String[] { Format(StarDate, new String(new char[] { format }), sdfi) };
                    break;
                default:
                    throw new NotImplementedException();
                    //throw new FormatException(StarLEnvironment.GetResourceString("Format_InvalidString"));

            }
            return (results);
        }

        internal static String[] GetAllStarDates(StarDate StarDate, StarCulture sdfi)
        {
            List<String> results = new List<String>(DEFAULT_ALL_StarDateS_SIZE);

            for (int i = 0; i < allStandardFormats.Length; i++)
            {
                String[] strings = GetAllStarDates(StarDate, allStandardFormats[i], sdfi);
                for (int j = 0; j < strings.Length; j++)
                {
                    results.Add(strings[j]);
                }
            }
            String[] value = new String[results.Count];
            results.CopyTo(0, value, 0, results.Count);
            return (value);
        }

        // This is a placeholder for an MDA to detect when the user is using a
        // local StarDate with a format that will be interpreted as UTC.
        internal static void InvalidFormatForLocal(String format, StarDate StarDate)
        {
        }

        // This is an MDA for cases when the user is using a local format with
        // a Utc StarDate.
        [System.Security.SecuritySafeCritical]  // auto-generated
        internal static void InvalidFormatForUtc(String format, StarDate StarDate)
        {
#if MDA_SUPPORTED
            Mda.StarDateInvalidLocalFormat();
#endif
        }


    }

    internal class StringBuilderCache
    {
        internal static StringBuilder Acquire(int rfc1123FormatLength)
        {
            throw new NotImplementedException();
        }

        internal static StringBuilder Acquire()
        {
            throw new NotImplementedException();
        }

        internal static string GetStringAndRelease(StringBuilder result)
        {
            ////////////Console.WriteLine("GetStringAndRelease is not implemented yet");
            return result.ToString();
        }
    }
}