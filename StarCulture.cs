// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==


using System;
using System.Security;
using System.Threading;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Security.Permissions;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Text;
using System.Diagnostics.Contracts;
using System.Runtime.CompilerServices;
using System.IO;
using StarCalendar;
//using System.Globalization;

namespace StarCalendar
{


    //
    // Flags used to indicate different styles of month names.
    // This is an internal flag used by internalGetMonthName().
    // Use flag here in case that we need to provide a combination of these styles
    // (such as month name of a leap Year in genitive form.  Not likely for now,
    // but would like to keep the option open).
    //

    [Flags]
    internal enum MonthNameStyles
    {
        Regular = 0x00000000,
        Genitive = 0x00000001,
        LeapYear = 0x00000002,
    }

    //
    // Flags used to indicate special rule used in parsing/formatting
    // for a specific StarCulture instance.
    // This is an internal flag.
    //
    // This flag is different from MonthNameStyles because this flag
    // can be expanded to accommodate parsing behaviors like CJK month names
    // or alternative month names, etc.

    [Flags]
    internal enum StarDateFormatFlags
    {
        None = 0x00000000,
        UseGenitiveMonth = 0x00000001,
        UseLeapYearMonth = 0x00000002,
        UseSpacesInMonthNames = 0x00000004, // Has spaces or non-breaking space in the month names.
        UseHebrewRule = 0x00000008,   // Format/Parse using the Hebrew calendar rule.
        UseSpacesInDayNames = 0x00000010,   // Has spaces or non-breaking space in the day names.
        UseDigitPrefixInTokens = 0x00000020,   // Has token starting with numbers.

        NotInitialized = -1,
    }


    [Serializable]
    [System.Runtime.InteropServices.ComVisible(true)]
    public sealed class StarCulture : ICloneable, IFormatProvider
    {
        private static Dictionary<string, StarCulture> dict = getformats();
        public static StarCulture InvariantCulture = dict["English"];
        internal bool m_isInherited = false;
        private readonly bool v;
        internal static StarCulture CurrentCulture = dict["English"];
        private StarCulture starDateInfo;
        private IFormatProvider formatProvider;
        [NonSerialized]
        private string[] monthGenitives;
        private int iFIRSTWEEKOFYEAR;
        [NonSerialized]
        public string TimeSeparator = ":";
        private static StarCulture Symbol;
        [NonSerialized]
        private string langfam;
        [NonSerialized]
        private string sNativeName;
        [NonSerialized]
        private string notes;
        [NonSerialized]
        private string[] saDayNames = new string[7];
        [NonSerialized]
        private List<string> months;
        [NonSerialized]
        private List<string> saMonthGenitiveNames;
        [NonSerialized]
        private List<string> misc;
        [NonSerialized]
        private string dateSeparator1 = "-";


        public StarCulture(string line)
        {
            string[] n = line.Split(',');
            //this.CultureName = n[0];
            int i = 0;
            while (i < n.Length)
            {
                switch (i)
                {
                    case 0:
                        this.CultureName = n[i];
                        if (CultureName == "English")
                        {
                            StarCulture.InvariantCulture = this;
                        }
                        if (CultureName == "Symbol")
                        {
                            StarCulture.Symbol = this;
                        }
                        break;
                    case 1:
                        this.langfam = n[i];
                        break;
                    case 2:
                        this.sNativeName = n[i];
                        break;
                    case 3:
                        this.SISO639LANGNAME = n[i];
                        this.ISO = new List<string> { n[i] };
                        break;
                    case 4:
                    case 5:
                    case 6:
                        this.ISO.Add(n[i]);
                        break;
                    case 7:
                        this.notes = n[i];
                        break;
                    case 8:
                        this.saDayNames[1] = n[i];
                        break;
                    case 9:
                        this.saDayNames[2] = n[i];
                        break;
                    case 10:
                        this.saDayNames[3] = n[i];
                        break;
                    case 11:
                        this.saDayNames[4] = n[i];
                        break;
                    case 12:
                        this.saDayNames[5] = n[i];
                        break;
                    case 13:
                        this.saDayNames[6] = n[i];
                        break;
                    case 14:
                        this.saDayNames[0] = n[i];
                        break;
                    case 15:
                        this.months = new List<string>() { n[i] };
                        break;
                    case 16:
                    case 17:
                    case 18:
                    case 19:
                    case 20:
                    case 21:
                    case 22:
                    case 23:
                    case 24:
                    case 25:
                    case 26:
                    case 27:
                    case 28:
                        this.months.Add(n[i]);
                        break;
                    case 29:
                        this.saMonthGenitiveNames = new List<string> { n[i] };
                        break;
                    case 30:
                    case 31:
                    case 32:
                    case 33:
                    case 34:
                    case 35:
                    case 36:
                    case 37:
                    case 38:
                    case 39:
                    case 40:
                    case 41:
                    case 42:
                        this.saMonthGenitiveNames.Add(n[i]);
                        break;
                    case 43:
                        this.SAM1159 = n[i];
                        break;
                    case 44:
                        this.SPM2359 = n[i];
                        break;
                    case 45:
                        this.TimeSeparator = n[i];
                        break;
                    case 46:
                        this.dateSeparator1 = n[i];
                        break;
                    case 47:
                        this.misc = new List<string>() { n[i] };
                        break;
                    case 48:
                    case 49:
                    case 50:
                    case 51:
                    case 52:
                    case 53:
                    case 54:
                    case 55:
                    case 56:
                    case 57:
                    case 58:
                    case 59:
                    default:
                        this.misc.Add(n[i]);
                        break;
                }
                i++;
            }

        }

        public override string ToString()
        {
            return this.SISO639LANGNAME + " " + this.sNativeName;
        }

        public StarCulture(string line, bool v) : this(line)
        {
            this.v = v;
        }

        internal string month(int m)
        {
            return this.months[m];
        }

        internal string weekday(int d)
        {
            return this.saDayNames[d - 1];
        }

        internal static StarCulture GetLocale(string lang)
        {
            return dict[lang];
        }

        internal string StarDateString(StarDate dt, string format)
        {
            //////Console.WriteLine(this.CultureName);
            //////Console.WriteLine(this == null);
            return StarDateFormat.Format(dt, format, this);
        }

        //internal static StarCulture InvariantCulture;
        //internal StarDateFormat DateTimeFormat;
        //private StarDateFormat starDateFormat;
        //private static StarCulture currentCulture/* = dict["English"];*/
        //private StarDateFormat starDateFormat;
        //private static object invariantCulture;

        //public static StarCulture CurrentCulture
        //{
        //    get
        //    {
        //        return currentCulture;
        //    }

        //    internal set
        //    {
        //        currentCulture = value;
        //    }
        //}
        public StarDateFormat StarDateFormat
        {
            get
            {


                return new StarDateFormat(AbbreviatedMonthNames, AbbreviatedDayNames);
            }

            //internal set
            //{
            //    starDateFormat = value;
            //}
        }

        private string[] AbbreviatedDayNames
        {
            get
            {
                if (saAbbrevDayNames1 == null)
                {
                    string[] vs = new string[7];
                    int i = 1;
                    while (i < vs.Length)
                    {
                        vs[i] = abbreviate(weekday(i));
                        if (vs[i] == "")
                        {
                            vs[i] = InvariantCulture.AbbreviatedDayNames[i];
                        }
                        i++;
                    }
                    saAbbrevDayNames1 = vs;
                }
                return saAbbrevDayNames1;
            }
            set
            {
                saAbbrevDayNames1 = value;
            }
        }

        public string[] SuperShortDayNames
        {
            get
            {
                if (superShortDayNames == null)
                {
                    string[] days = new string[7];
                    int i = 0;
                    while (i < days.Length)
                    {
                        days[i] = AbbreviatedDayNames[i].Substring(0, 2);
                        i++;
                    }
                    superShortDayNames = days;
                }
                return superShortDayNames;
            }

            private set
            {
                superShortDayNames = value;
            }
        }



        private string abbreviate(string v)
        {
            string a = "";
            try
            {
                a = a + v[0];
                try
                {
                    a = a + v[1];
                    try
                    {
                        a = a + v[2];
                    }
                    catch (IndexOutOfRangeException)
                    {
                        //rrrr
                    }
                }
                catch (IndexOutOfRangeException)
                {

                }
            }
            catch (IndexOutOfRangeException)
            {

            }
            return a;
        }

        public string[] AbbreviatedMonthNames
        {
            get
            {
                if (_abbreviatedMonthNames == null)
                {
                    string[] vs = new string[this.months.Count];
                    int i = 0;
                    while (i < vs.Length)
                    {
                        vs[i] = abbreviate(months[i]);
                        if (vs[i] == "")
                        {
                            vs[i] = InvariantCulture.AbbreviatedMonthNames[i];
                        }
                        i++;
                    }
                    _abbreviatedMonthNames = vs;
                }

                return _abbreviatedMonthNames;
            }
        }

        public string CultureName { get => cultureName; internal set => cultureName = value; }
        public string SISO639LANGNAME { get => sISO639LANGNAME; internal set => sISO639LANGNAME = value; }

        [NonSerialized]
        private List<string> ISO;

        //private Dictionary<int, string> ISO;

        //public StarCulture m_cultureData
        //{
        //    get
        //    {
        //        return this;
        //    }
        //}
        public int IFIRSTDAYOFWEEK { get; internal set; }
        public int IFIRSTWEEKOFYEAR
        {
            get
            {
                return iFIRSTWEEKOFYEAR;
            }

            internal set
            {
                iFIRSTWEEKOFYEAR = value;
            }
        }
        public string SAM1159
        {
            get
            {
                if (sAM1159 == null)
                {
                    sAM1159 = InvariantCulture.SAM1159;
                }
                return sAM1159;
            }

            internal set
            {
                sAM1159 = value;
            }
        }
        public string SPM2359
        {
            get
            {
                if (sPM2359 == null)
                {
                    sPM2359 = InvariantCulture.SPM2359;
                }
                return sPM2359;
            }

            internal set
            {
                sPM2359 = value;
            }
        }

        //[NonSerialized]
        //private string TimeSeparator;

        //public string TimeSeparator { get { return TimeSeparator; } internal set => TimeSeparator = value; }
        public string[] LongTimes
        {
            get
            {
                if (this._longtimes == null)
                {
                    this._longtimes = InvariantCulture._longtimes;
                }
                return _longtimes;
            }

            internal set
            {
                _longtimes = value;
            }
        }
        public string[] ShortTimes { get => shortTimes; internal set => shortTimes = value; }
        public bool UseUserOverride { get; internal set; }
        public StarCulture StarDateInfo
        {
            get
            {
                return starDateInfo;
            }

            internal set
            {
                starDateInfo = value;
            }
        }
        public int[] CalendarIds { get; internal set; }
        public IFormatProvider FormatProvider
        {
            get
            {
                if (formatProvider == null)
                {
                    formatProvider = System.Globalization.NumberFormatInfo.InvariantInfo;
                }
                return formatProvider;
            }

            private set
            {
                formatProvider = value;
            }
        }

        public string[] GenitiveMonthNames
        {
            get
            {
                string[] gen = new string[saMonthGenitiveNames.Count];
                int i = 0;
                while (i < saMonthGenitiveNames.Count)
                {
                    if (saMonthGenitiveNames[i] == "")
                    {
                        gen[i] = dict["Symbol"].saMonthGenitiveNames[i];
                    }
                    else
                    {
                        gen[i] = saMonthGenitiveNames[i];
                    }
                    i++;
                }
                return gen;
            }

            private set
            {
                monthGenitives = value;
            }
        }



        internal IFormatProvider GetFormat(Type type)
        {
            return this.FormatProvider;
        }

        internal static StarCulture GetCultureInfo(string cultureName)
        {
            throw new NotImplementedException();
        }

        //internal string[] AbbreviatedDayNames(object iD)
        //{
        //    return AbbreviatedDayNames;
        //}

        //internal string[] SuperShortDayNames(object iD)
        //{
        //    return SuperShortDayNames();
        //}

        //private string[] SuperShortDayNames()
        //{
        //    throw new NotImplementedException();
        //}

        //internal string[] DayNames(int iD)
        //{
        //    return DayNames();
        //}

        private string[] DayNames
        {
            get
            {
                string[] vs = new string[7];
                int i = 1;
                while (i < vs.Length)
                {
                    vs[i] = weekday(i);
                    i++;
                }
                return vs;
            }
        }

        //internal string[] AbbreviatedMonthNames(object iD)
        //{
        //    return AbbreviatedMonthNames;
        //}

        //internal string[] MonthNames(object iD)
        //{
        //    return MonthNames();
        //}

        public string[] MonthNames
        {
            get
            {
                if (saMonthNames == null)
                {
                    string[] vs = new string[this.months.Count];
                    int i = 0;
                    while (i < vs.Length)
                    {
                        vs[i] = months[i];
                        i++;
                    }
                    saMonthNames = vs;
                }
                return saMonthNames;
            }
            set
            {
                saMonthNames = value;
            }
        }

        //public string[] m_genitiveAbbreviatedMonthNames { get; private set; }

        internal string GetDateSeparator(int calendarID)
        {
            throw new NotImplementedException();
        }

        internal string[] LongDates(int calendarID)
        {
            throw new NotImplementedException();
        }

        internal string[] ShortDates(int calendarID)
        {
            return this.saShortDates;
        }

        internal string[] YearMonths()
        {
            throw new NotImplementedException();
        }

        internal static StarCulture GetCultureData(string m_name, bool m_useUserOverride)
        {
            throw new NotImplementedException();
        }

        internal static void CheckDomainSafetyObject(StarCulture calendar, StarCulture starDateFormatInfo)
        {
            throw new NotImplementedException();
        }

        internal IFormatProvider GetFormat()
        {
            return this.FormatProvider;
        }

        //internal string[] AbbreviatedGenitiveMonthNames(int iD)
        //{
        //    return AbbreviatedGenitiveMonthNames();
        //}

        private string[] AbbreviatedGenitiveMonthNames
        {
            get
            {
                if (m_genitiveAbbreviatedMonthNames == null)
                {
                    string[] gen = new string[15];
                    int i = 0;
                    while (i < 15)
                    {
                        if (saMonthGenitiveNames[i] == "")
                        {
                            gen[i] = abbreviate(dict["Symbol"].saMonthGenitiveNames[i]);
                        }
                        else
                        {
                            gen[i] = abbreviate(saMonthGenitiveNames[i]);
                        }
                        i++;
                    }
                    m_genitiveAbbreviatedMonthNames = gen;
                }
                return m_genitiveAbbreviatedMonthNames;
            }
            set
            {
                m_genitiveAbbreviatedMonthNames = value;
            }
        }

        //internal string[] GenitiveMonthNames(int iD)
        //{
        //    return this.GenitiveMonthNames;
        //}

        //internal string[] AbbreviatedEnglishEraNames(int iD)
        //{
        //    throw new NotImplementedException();
        //}

        //internal string MonthDay(int iD)
        //{
        //    throw new NotImplementedException();
        //}

        //internal string[] LeapYearMonthNames(int iD)
        //{
        //    throw new NotImplementedException();
        //}

        //internal string CalendarName(int iD)
        //{
        //    throw new NotImplementedException();
        //}

        private static Dictionary<string, StarCulture> getformats()
        {
            int counter = 0;
            string line;
            Dictionary<string, StarCulture> formats = new Dictionary<string, StarCulture>();
            string path = "Languages.csv";
            //int lastslash = Gedcom.LastIndexOf('/');
            //string Filename = Gedcom.Substring(lastslash + 1);
            //Gedson ged = new Gedson();
            System.IO.StreamReader file = new StreamReader(path);
            while ((line = file.ReadLine()) != null)
            {
                ////////Console.WriteLine(line);
                StarCulture form = new StarCulture(line);
                formats.Add(form.CultureName, form);
                counter++;
            }
            // Set our default/gregorian US calendar data
            // Calendar IDs are 1-based, arrays are 0 based.
            //CalendarData invariant = new CalendarData();

            // Set default data for calendar
            // Note that we don't load resources since this IS NOT supposed to change (by definition)
            InvariantCulture.sNativeName = "Gregorian Calendar";  // Calendar Name

            // Year
            //InvariantCulture.iTwoDigitYearMax = 2029; // Max 2 digit Year (for Y2K bug data entry)

            // Formats
            InvariantCulture.saShortDates = new String[] { "MM/dd/yyyy", "yyyy-MM-dd" };          // short date format
            InvariantCulture.saLongDates = new String[] { "dddd, dd MMMM yyyy" };                 // long date format
            InvariantCulture.saYearMonths = new String[] { "yyyy MMMM" };                         // Year month format
            InvariantCulture.sMonthDay = "MMMM dd";                                            // Month day pattern

            // Calendar Parts Names
            //InvariantCulture.saEraNames = new String[] { "A.D." };     // Era names
            //InvariantCulture.saAbbrevEraNames = new String[] { "AD" };      // Abbreviated Era names
            //InvariantCulture.saAbbrevEnglishEraNames = new String[] { "AD" };     // Abbreviated era names in English
            InvariantCulture.saDayNames = new String[] { "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" };// day names
            InvariantCulture.AbbreviatedDayNames = new String[] { "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" };     // abbreviated day names
            InvariantCulture.SuperShortDayNames = new String[] { "Su", "Mo", "Tu", "We", "Th", "Fr", "Sa" };      // The super short day names
            InvariantCulture.MonthNames = new String[] { "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus",
                                                            "Gemini", "Karkino", "Leo", "Virgo", "Libra", "Scorpio", "Ophiuchus", "Horus"}; // month names
            InvariantCulture.m_genitiveAbbreviatedMonthNames = new String[] { "Sag", "Cap", "Aqu", "Pis", "Ari", "Tau",
                                                            "Gem", "Kar", "Leo", "Vir", "Lib", "Sco", "Oph", "Hor"}; // abbreviated month names
                                                                                                                     // Time
            InvariantCulture.TimeSeparator = ":";
            InvariantCulture.SAM1159 = "AM";                   // AM designator
            InvariantCulture.SPM2359 = "PM";                   // PM designator
            InvariantCulture._longtimes = new string[] { "HH:mm:ss" };                             // time format
            InvariantCulture._saShortTimes = new string[] { "HH:mm", "hh:mm tt", "H:mm", "h:mm tt" }; // short time format
            InvariantCulture._saDurationFormats = new string[] { "HH:mm:ss" };                             // time duration format
            InvariantCulture.m_genitiveAbbreviatedMonthNames = InvariantCulture.AbbreviatedGenitiveMonthNames;    // Abbreviated genitive month names (same as abbrev month names for invariant)
                                                                                                                  //InvariantCulture.saLeapYearMonthNames = InvariantCulture.saMonthNames;              // leap Year month names are unused in Gregorian English (invariant)
                                                                                                                  //    public string SAM1159 { get; internal set; }
                                                                                                                  //public string SPM2359 { get; internal set; }
            InvariantCulture.bUseUserOverrides = false;

            // Calendar was built, go ahead and assign it...            
            //Invariant = invariant;
            return formats;
        }

        //

        public IFormatProvider GetFormatProvider()
        {
            return this.FormatProvider;
        }

        internal string[] GetDayNames()
        {
            return this.DayNames;
        }


        //
        // Note, some fields are derived so don't really need to be serialized, but we can't mark as
        // optional because Whidbey was expecting them.  Post-Arrowhead we could fix that
        // once Whidbey serialization is no longer necessary.
        //

        // cache for the invariant culture.
        // invariantInfo is constant irrespective of your current culture.
        //private static volatile StarCulture invariantInfo;

        // an index which points to a record in Culture Data Table.
        //[NonSerialized] private StarCulture m_cultureData;

        // The culture name used to create this sdfi.
        [OptionalField(VersionAdded = 2)]
        [NonSerialized]
        internal String m_name = null;

        // The language name of the culture used to create this sdfi.
        [NonSerialized] private String m_langName = null;

        // CompareInfo usually used by the parser.
        //[NonSerialized] private CompareInfo m_compareInfo = null;

        // Culture matches current sdfi. mainly used for string comparisons during parsing.
        [NonSerialized] private StarCulture m_cultureInfo = null;

        //
        // Caches for various properties.
        //

        // 

        [NonSerialized]
        internal String amDesignator = null;
        [NonSerialized]
        internal String pmDesignator = null;
        [OptionalField(VersionAdded = 1)]
        [NonSerialized]
        internal String dateSeparator = null;            // derived from short date (whidbey expects, arrowhead doesn't)
        [OptionalField(VersionAdded = 1)]
        [NonSerialized]
        internal String generalShortTimePattern = null;     // short date + short time (whidbey expects, arrowhead doesn't)
        [OptionalField(VersionAdded = 1)]
        [NonSerialized]
        internal String generalLongTimePattern = null;     // short date + long time (whidbey expects, arrowhead doesn't)
        [OptionalField(VersionAdded = 1)]
        [NonSerialized]
        //internal String TimeSeparator = null;            // derived from long time (whidbey expects, arrowhead doesn't)
        internal String monthDayPattern = null;
        [OptionalField(VersionAdded = 2)]                   // added in .NET Framework Release {2.0SP1/3.0SP1/3.5RTM}
        //internal String StarDateOffsetPattern = null;

        //
        // The following are constant values.
        //
        internal const String rfc1123Pattern = "ddd, dd MMM yyyy HH':'mm':'ss 'GMT'";

        // The sortable pattern is based on ISO 8601.
        internal const String sortableStarDatePattern = "yyyy'-'MM'-'dd'T'HH':'mm':'ss";
        internal const String universalSortableStarDatePattern = "yyyy'-'MM'-'dd HH':'mm':'ss'Z'";

        //
        // The following are affected by calendar settings.
        //

        internal int firstDayOfWeek = -1;
        internal int calendarWeekRule = -1;

        [OptionalField(VersionAdded = 1)]
        [NonSerialized]
        internal String fullStarDatePattern = null;        // long date + long time (whidbey expects, arrowhead doesn't)

        [NonSerialized]
        internal String[] saAbbrevDayNames1 = null;

        [OptionalField(VersionAdded = 2)]
        [NonSerialized]
        internal String[] superShortDayNames = null;
        [NonSerialized]
        internal String[] dayNames = null;
        [NonSerialized]
        private String[] _abbreviatedMonthNames = null;
        [NonSerialized]
        internal String[] monthNames = null;
        // Cache the genitive month names that we retrieve from the data table.
        [OptionalField(VersionAdded = 2)]
        [NonSerialized]
        internal String[] genitiveMonthNames = null;

        // Cache the abbreviated genitive month names that we retrieve from the data table.
        [OptionalField(VersionAdded = 2)]
        [NonSerialized]
        internal String[] m_genitiveAbbreviatedMonthNames = null;

        //private string SAM1159;
        //private string SPM2359;
        [NonSerialized]
        private string[] _longtimes;
        [NonSerialized]
        private string[] _saShortTimes;
        [NonSerialized]
        private string[] _saDurationFormats;

        // Cache the month names of a leap Year that we retrieve from the data table.
        [OptionalField(VersionAdded = 2)]
        [NonSerialized]
        internal String[] leapYearMonthNames = null;

        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]

        // The "default" Date/time patterns
        [NonSerialized]
        internal String longDatePattern = null;
        [NonSerialized]
        internal String shortDatePattern = null;
        [NonSerialized]
        internal String yearMonthPattern = null;
        [NonSerialized]
        internal String longTimePattern = null;
        [NonSerialized]
        internal String shortTimePattern = null;

        // These are Whidbey-serialization compatable arrays (eg: default not included)
        // "all" is a bit of a misnomer since the "default" pattern stored above isn't
        // necessarily a member of the list
        [OptionalField(VersionAdded = 3)]
        [NonSerialized]
        private String[] allYearMonthPatterns = null;   // This was wasn't serialized in Whidbey
        [NonSerialized]
        internal String[] allShortDatePatterns = null;
        [NonSerialized]
        internal String[] allLongDatePatterns = null;
        [NonSerialized]
        internal String[] allShortTimePatterns = null;
        [NonSerialized]
        internal String[] allLongTimePatterns = null;

        // Cache the era names for this StarCulture instance.
        [NonSerialized]
        internal String[] m_eraNames = null;
        [NonSerialized]
        internal String[] m_abbrevEraNames = null;
        [NonSerialized]
        internal String[] m_abbrevEnglishEraNames = null;

        internal int[] optionalCalendars = null;

        private const int DEFAULT_ALL_StarDateS_SIZE = 132;

        // StarCulture updates this
        internal bool m_isReadOnly = false;

        // This flag gives hints about if formatting/parsing should perform special code path for things like
        // genitive form or leap Year month names.
        [OptionalField(VersionAdded = 2)]
        internal StarDateFormatFlags formatFlags = StarDateFormatFlags.NotInitialized;
        //internal static bool preferExistingTokens = InitPreferExistingTokens();


        //        [System.Security.SecuritySafeCritical]
        //        static bool InitPreferExistingTokens()
        //        {
        //            bool ret = false;
        //#if !FEATURE_CORECLR
        //            ret = StarDate.LegacyParseMode();
        //#endif
        //            return ret;
        //        }


        // 
        //private String CultureName
        //{
        //    get
        //    {
        //        if (m_name == null)
        //        {
        //            m_name = this.CultureName;
        //        }
        //        return (m_name);
        //    }
        //}

        private StarCulture Culture
        {
            get
            {
                if (m_cultureInfo == null)
                {
                    m_cultureInfo = StarCulture.GetCultureInfo(this.CultureName);
                }
                return m_cultureInfo;
            }
        }

        // 
        private String LanguageName
        {
            [System.Security.SecurityCritical]  // auto-generated
            get
            {
                if (m_langName == null)
                {
                    m_langName = this.SISO639LANGNAME;
                }
                return (m_langName);
            }
        }

        ////////////////////////////////////////////////////////////////////////////
        //
        // Create an array of string which contains the abbreviated day names.
        //
        ////////////////////////////////////////////////////////////////////////////

        private String[] internalGetAbbreviatedDayOfWeekNames()
        {
            //if (this.saAbbrevDayNames1 == null)
            //{
            //    // Get the abbreviated day names for our current calendar
            //    this.saAbbrevDayNames1 = this.AbbreviatedDayNames;
            //    Contract.Assert(this.saAbbrevDayNames1.Length == 7, "[StarCulture.GetAbbreviatedDayOfWeekNames] Expected 7 day names in a week");
            //}
            return this.AbbreviatedDayNames;
        }

        ////////////////////////////////////////////////////////////////////////
        //
        // Action: Returns the string array of the one-letter day of week names.
        // Returns:
        //  an array of one-letter day of week names
        // Arguments:
        //  None
        // Exceptions:
        //  None
        //
        ////////////////////////////////////////////////////////////////////////

        //private String[] internalGetSuperShortDayNames()
        //{
        //    if (this.superShortDayNames == null)
        //    {
        //        // Get the super short day names for our current calendar
        //        this.superShortDayNames = this.SuperShortDayNames;
        //        Contract.Assert(this.superShortDayNames.Length == 7, "[StarCulture.internalGetSuperShortDayNames] Expected 7 day names in a week");
        //    }
        //    return (this.superShortDayNames);
        //}

        ////////////////////////////////////////////////////////////////////////////
        //
        // Create an array of string which contains the day names.
        //
        ////////////////////////////////////////////////////////////////////////////

        private String[] internalGetDayOfWeekNames()
        {
            if (this.dayNames == null)
            {
                // Get the day names for our current calendar
                //////Console.WriteLine(this);
                ////////Console.WriteLine(Calendar);
                //////Console.WriteLine;
                ////////Console.WriteLine("What is Null here");
                var d = this.GetDayNames();
                foreach (var entry in d)
                {
                    //////Console.WriteLine(entry);
                }
                //Something is a null reference here and I don't understand it
                this.dayNames = this.DayNames;
                Contract.Assert(this.dayNames.Length == 7, "[StarCulture.GetDayOfWeekNames] Expected 7 day names in a week");
            }
            return (this.dayNames);
        }

        ////////////////////////////////////////////////////////////////////////////
        //
        // Create an array of string which contains the abbreviated month names.
        //
        ////////////////////////////////////////////////////////////////////////////

        private String[] internalGetAbbreviatedMonthNames()
        {
            if (this._abbreviatedMonthNames == null)
            {
                // Get the month names for our current calendar
                this._abbreviatedMonthNames = this.AbbreviatedMonthNames;
                //Contract.Assert(this._abbreviatedMonthNames.Length == 12 || this._abbreviatedMonthNames.Length == 13,
                //    "[StarCulture.GetAbbreviatedMonthNames] Expected 12 or 13 month names in a Year");
            }
            return (this._abbreviatedMonthNames);
        }


        ////////////////////////////////////////////////////////////////////////////
        //
        // Create an array of string which contains the month names.
        //
        ////////////////////////////////////////////////////////////////////////////

        private String[] internalGetMonthNames()
        {
            return this.MonthNames;
        }

        //    return (this.monthNames);
        //}


        //
        // Invariant StarCulture doesn't have user-overriden values
        // Default calendar is gregorian
        //public StarCulture()
        //: this(StarCulture.InvariantCulture.m_cultureData,
        //        GregorianCalendar.GetDefaultInstance())
        //        {
        //        }

        //            #region Serialization
        //            // The following fields are defined to keep the serialization compatibility with .NET V1.0/V1.1.
        //            [OptionalField(VersionAdded = 1)]
        //        private int CultureID;
        //        [OptionalField(VersionAdded = 1)]
        //        private bool m_useUserOverride;
        //#if !FEATURE_CORECLR
        //        [OptionalField(VersionAdded = 1)]
        //        private bool bUseCalendarInfo;
        //        [OptionalField(VersionAdded = 1)]
        //        private int nDataItem;
        //        [OptionalField(VersionAdded = 2)]
        //        internal bool m_isDefaultCalendar;                // NEVER USED, DO NOT USE THIS! (Serialized in Whidbey)
        //        [OptionalField(VersionAdded = 2)]
        //        private static volatile Hashtable s_calendarNativeNames;   // NEVER USED, DO NOT USE THIS! (Serialized in Whidbey)
        //#endif // !FEATURE_CORECLR

        //        // This was synthesized by Whidbey so we knew what words might appear in the middle of a date string
        //        // Now we always synthesize so its not helpful
        //        [OptionalField(VersionAdded = 1)]
        //        internal String[] m_dateWords = null;               // calculated, no need to serialze  (whidbey expects, arrowhead doesn't)

        //            [OnSerializing]
        //        private void OnSerializing(StreamingContext ctx)
        //        {
        //#if FEATURE_USE_LCID
        //            CultureID           = this.m_cultureData.ILANGUAGE;       // Used for serialization compatibility with Whidbey which didn't always serialize the name
        //#endif
        //            m_useUserOverride = this.UseUserOverride;

        //            // make sure the m_name is initialized.
        //            m_name = this.CultureName;

        //#if !FEATURE_CORECLR
        //            if (s_calendarNativeNames == null)
        //                s_calendarNativeNames = new Hashtable();
        //#endif // FEATURE_CORECLR

        //            // Important to initialize these fields otherwise we may run into exception when deserializing on Whidbey
        //            // because Whidbey try to initialize some of these fields using calendar data which could be null values
        //            // and then we get exceptions.  So we call the accessors to force the caches to get loaded.
        //            Object o;
        //            o = this.LongTimePattern;
        //            o = this.LongDatePattern;
        //            o = this.ShortTimePattern;
        //            o = this.ShortDatePattern;
        //            o = this.YearMonthPattern;
        //            o = this.AllLongTimePatterns;
        //            o = this.AllLongDatePatterns;
        //            o = this.AllShortTimePatterns;
        //            o = this.AllShortDatePatterns;
        //            o = this.AllYearMonthPatterns;
        //        }
        //        #endregion Serialization

        // Returns a default StarCulture that will be universally
        // supported and constant irrespective of the current culture.
        // Used by FromString methods.
        //

        //public static StarCulture InvariantCulture
        //{
        //    get
        //    {
        //        Contract.Ensures(Contract.Result<StarCulture>() != null);
        //        if (invariantInfo == null)
        //        {
        //            StarCulture info = new StarCulture();
        //            info.Calendar.SetReadOnlyState(true);
        //            info.m_isReadOnly = true;
        //            invariantInfo = info;
        //        }
        //        return (invariantInfo);
        //    }
        //}

        // Returns the current culture's StarCulture.  Used by Parse methods.
        //

        //public static StarCulture CurrentInfo
        //{
        //    get
        //    {
        //        //////Console.WriteLine("Breakpoint");
        //        Contract.Ensures(Contract.Result<StarCulture>() != null);
        //        StarCulture culture = StarCulture.CurrentCulture;
        //        if (!culture.m_isInherited)
        //        {
        //            StarCulture info = culture.StarDateInfo;
        //            if (info != null)
        //            {
        //                return info;
        //            }
        //        }
        //        return culture.StarDateInfo;
        //    }
        //}


        //public static StarCulture GetInstance(IFormatProvider provider)
        //{
        //    // Fast case for a regular StarCulture
        //    StarCulture info;
        //    StarCulture cultureProvider = provider as StarCulture;
        //    if (cultureProvider != null && !cultureProvider.m_isInherited)
        //    {
        //        throw new NotImplementedException(); // throw new NotImplementedException();
        //        //return cultureProvider.StarDateFormat;
        //    }
        //    // Fast case for a sdfi;
        //    info = provider as StarCulture;
        //    if (info != null)
        //    {
        //        return info;
        //    }
        //    // Wasn't cultureInfo or sdfi, do it the slower way
        //    if (provider != null)
        //    {
        //        info = provider.GetFormat(typeof(StarCulture)) as StarCulture;
        //        if (info != null)
        //        {
        //            return info;
        //        }
        //    }
        //    // Couldn't get anything, just use currentInfo as fallback
        //    return CurrentInfo;
        //}

        internal string GetEraName(StarDate dt)
        {
            throw new NotImplementedException();
        }

        //public Object GetFormat(Type formatType)
        //{
        //    return (formatType == typeof(StarCulture) ? this : null);
        //}


        //public Object Clone()
        //{
        //    StarCulture n = (StarCulture)MemberwiseClone();
        //    // We can use the data member calendar in the setter, instead of the property StarCulture,
        //    // since the cloned copy should have the same state as the original copy.
        //    n.calendar = (StarCulture)this.Calendar.Clone();
        //    n.m_isReadOnly = false;
        //    return n;
        //}


        public String AMDesignator
        {
            //#if FEATURE_CORECLR
            //            [System.Security.SecuritySafeCritical]  // auto-generated
            //#endif
            get
            {
                //#if FEATURE_CORECLR
                //                if (this.amDesignator == null)
                //                {
                //                    this.amDesignator = this.m_cultureData.SAM1159;
                //                }
                //#endif
                //Contract.Assert(this.amDesignator != null, "StarCulture.AMDesignator, amDesignator != null");
                if (this.amDesignator == null)
                {
                    this.amDesignator = "AM";
                }
                return (this.amDesignator);
            }

            set
            {
                //if (IsReadOnly)
                //    throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
                //if (value == null)
                //{
                //    throw new NotImplementedException(); // throw new ArgumentNullException("value",
                //        //LEnvironment.GetResourceString("ArgumentNull_String"));
                //}
                Contract.EndContractBlock();
                ClearTokenHashTable();
                amDesignator = value;
            }
        }


        //public StarCulture Calendar
        //{
        //    get
        //    {
        //        if (this.calendar == null)
        //        {
        //            this.calendar = new StarCulture(this);
        //        }
        //        //Contract.Ensures(Contract.Result<StarCulture>() != null);

        //        //Contract.Assert(this.calendar != null, "StarCulture.StarCulture: calendar != null");
        //        return (this.calendar);
        //    }

        //    set
        //    {
        //        if (IsReadOnly)
        //            throw new NotImplementedException(); // throw new NotImplementedException();
        //                                                 //throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
        //        if (value == null)
        //        {
        //            throw new NotImplementedException(); // throw new NotImplementedException();
        //            //throw new NotImplementedException(); // throw new ArgumentNullException("value",
        //            //    //LEnvironment.GetResourceString("ArgumentNull_Obj"));
        //        }
        //        Contract.EndContractBlock();
        //        if (value == calendar)
        //        {
        //            return;
        //        }

        //        //
        //        // Because the culture is agile object which can be attached to a thread and then thread can travel
        //        // to another app domain then we prevent attaching any customized object to culture that we cannot contol.
        //        //
        //        StarCulture.CheckDomainSafetyObject(value, this);

        //        for (int i = 0; i < this.OptionalCalendars.Length; i++)
        //        {
        //            if (this.OptionalCalendars[i] == value.ID)
        //            {
        //                // We can use this one, so do so.

        //                // Clean related properties if we already had a calendar set
        //                if (calendar != null)
        //                {
        //                    // clean related properties which are affected by the calendar setting,
        //                    // so that they will be refreshed when they are accessed next time.
        //                    //

        //                    // These properites are in the order as appearing in calendar.xml.
        //                    m_eraNames = null;
        //                    m_abbrevEraNames = null;
        //                    m_abbrevEnglishEraNames = null;

        //                    monthDayPattern = null;

        //                    dayNames = null;
        //                    saAbbrevDayNames1 = null;
        //                    superShortDayNames = null;
        //                    monthNames = null;
        //                    _abbreviatedMonthNames = null;
        //                    genitiveMonthNames = null;
        //                    m_genitiveAbbreviatedMonthNames = null;
        //                    leapYearMonthNames = null;
        //                    formatFlags = StarDateFormatFlags.NotInitialized;

        //                    allShortDatePatterns = null;
        //                    allLongDatePatterns = null;
        //                    allYearMonthPatterns = null;
        //                    StarDateOffsetPattern = null;

        //                    // The defaults need reset as well:
        //                    longDatePattern = null;
        //                    shortDatePattern = null;
        //                    yearMonthPattern = null;

        //                    // These properies are not in the OS data, but they are dependent on the values like shortDatePattern.
        //                    fullStarDatePattern = null; // Long date + long time
        //                    generalShortTimePattern = null; // short date + short time
        //                    generalLongTimePattern = null; // short date + long time

        //                    // Derived item that changes
        //                    dateSeparator = null;

        //                    // We don't need to do these because they are not changed by changing calendar
        //                    //      amDesignator
        //                    //      pmDesignator
        //                    //      TimeSeparator
        //                    //      longTimePattern
        //                    //      firstDayOfWeek
        //                    //      calendarWeekRule

        //                    // We don't need to clear these because they're only used for whidbey compat serialization
        //                    // the only values we use are the all...Patterns[0]
        //                    //      longDatePattern
        //                    //      shortDatePattern
        //                    //      yearMonthPattern

        //                    // remember to reload tokens
        //                    ClearTokenHashTable();
        //                }

        //                // Remember the new calendar
        //                calendar = value;
        //                InitializeOverridableProperties(this, ID);

        //                // We succeeded, return
        //                return;
        //            }
        //        }

        //        // The assigned calendar is not a valid calendar for this culture, throw
        //        throw new NotImplementedException(); // throw new NotImplementedException();
        //        //throw new NotImplementedException(); // throw new ArgumentOutOfRangeException("value", //LEnvironment.GetResourceString("Argument_InvalidCalendar"));
        //    }
        //}

        private int[] OptionalCalendars
        {
            get
            {
                if (this.optionalCalendars == null)
                {
                    this.optionalCalendars = this.CalendarIds;
                }
                return (this.optionalCalendars);
            }
        }

        /*=================================GetEra==========================
        **Action: Get the era value by parsing the name of the era.
        **Returns: The era value for the specified era name.
        **      -1 if the name of the era is not valid or not supported.
        **Arguments: eraName    the name of the era.
        **Exceptions: None.
        ============================================================================*/


        //public int GetEra(String eraName)
        //{
        //    if (eraName == null)
        //    {
        //        throw new NotImplementedException(); // throw new NotImplementedException();
        //    }
        //    Contract.EndContractBlock();

        //    // For Geo-----al reasons, the Era Name and Abbreviated Era Name
        //    // for ---- StarCulture on non----- SKU returns empty string (which
        //    // would be matched below) but we don't want the empty string to give
        //    // us an Era number
        //    // confer 85900 sdfi.GetEra("") should fail on all cultures
        //    if (eraName.Length == 0)
        //    {
        //        return (-1);
        //    }

        //    // The following is based on the assumption that the era value is starting from 1, and has a
        //    // serial values.
        //    // If that ever changes, the code has to be changed.

        //    // The calls to String.Compare should use the current culture for the string comparisons, but the
        //    // invariant culture when comparing against the english names.
        //    for (int i = 0; i < EraNames.Length; i++)
        //    {
        //        // Compare the era name in a case-insensitive way for the appropriate culture.
        //        if (m_eraNames[i].Length > 0)
        //        {
        //            if (String.Compare(eraName, m_eraNames[i], this.Culture, CompareOptions.IgnoreCase) == 0)
        //            {
        //                return (i + 1);
        //            }
        //        }
        //    }
        //    for (int i = 0; i < AbbreviatedEraNames.Length; i++)
        //    {
        //        // Compare the abbreviated era name in a case-insensitive way for the appropriate culture.
        //        if (String.Compare(eraName, m_abbrevEraNames[i], this.Culture, CompareOptions.IgnoreCase) == 0)
        //        {
        //            return (i + 1);
        //        }
        //    }
        //    for (int i = 0; i < AbbreviatedEnglishEraNames.Length; i++)
        //    {
        //        // this comparison should use the InvariantCulture.  The English name could have linguistically
        //        // interesting characters.
        //        if (String.Compare(eraName, m_abbrevEnglishEraNames[i], StringComparison.InvariantCultureIgnoreCase) == 0)
        //        {
        //            return (i + 1);
        //        }
        //    }
        //    return (-1);
        //}

        //internal String[] EraNames
        //{
        //    get
        //    {
        //        if (this.m_eraNames == null)
        //        {
        //            this.m_eraNames = this.m_cultureData.EraNames(StarCulture.ID); ;
        //        }
        //        return (this.m_eraNames);
        //    }
        //}

        /*=================================GetEraName==========================
        **Action: Get the name of the era for the specified era value.
        **Returns: The name of the specified era.
        **Arguments:
        **      era the era value.
        **Exceptions:
        **      ArguementException if the era valie is invalid.
        ============================================================================*/

        // Era names are 1 indexed
        //public String GetEraName(int era)
        //{
        //    if (era == StarCulture.CurrentEra)
        //    {
        //        era = StarCulture.CurrentEraValue;
        //    }

        //    // The following is based on the assumption that the era value is starting from 1, and has a
        //    // serial values.
        //    // If that ever changes, the code has to be changed.
        //    if ((--era) < EraNames.Length && (era >= 0))
        //    {
        //        return (m_eraNames[era]);
        //    }
        //    throw new NotImplementedException(); // throw new NotImplementedException();
        //}

        //internal String[] AbbreviatedEraNames
        //{
        //    get
        //    {
        //        if (this.m_abbrevEraNames == null)
        //        {
        //            this.m_abbrevEraNames = this.m_cultureData.AbbrevEraNames(StarCulture.ID);
        //        }
        //        return (this.m_abbrevEraNames);
        //    }
        //}

        //// Era names are 1 indexed
        //public String GetAbbreviatedEraName(int era)
        //{
        //    if (AbbreviatedEraNames.Length == 0)
        //    {
        //        // If abbreviation era name is not used in this culture,
        //        // return the full era name.
        //        return (GetEraName(era));
        //    }
        //    if (era == StarCulture.CurrentEra)
        //    {
        //        era = StarCulture.CurrentEraValue;
        //    }
        //    if ((--era) < m_abbrevEraNames.Length && (era >= 0))
        //    {
        //        return (m_abbrevEraNames[era]);
        //    }
        //    throw new NotImplementedException(); // throw new NotImplementedException();
        //}

        //internal String[] AbbreviatedEnglishEraNames
        //{
        //    get
        //    {
        //        if (this.m_abbrevEnglishEraNames == null)
        //        {
        //            Contract.Assert(StarCulture.ID > 0, "[StarCulture.AbbreviatedEnglishEraNames] Expected StarCulture.ID > 0");
        //            this.m_abbrevEnglishEraNames = this.m_cultureData.AbbreviatedEnglishEraNames(StarCulture.ID);
        //        }
        //        return (this.m_abbrevEnglishEraNames);
        //    }
        //}


        // Note that cultureData derives this from the short date format (unless someone's set this previously)
        // Note that this property is quite undesirable.
        //        public String GetDateSeparator
        //        {
        //            get
        //            {
        //#if FEATURE_CORECLR
        //                if (this.dateSeparator == null)
        //                {
        //                    this.dateSeparator = this.m_cultureData.GetDateSeparator(StarCulture.ID);
        //                }
        //#endif
        //                //Contract.Assert(this.dateSeparator != null, "StarCulture.GetDateSeparator, dateSeparator != null");
        //                //////Console.WriteLine("Contract.Assert(this.dateSeparator != null, " + " StarCulture.GetDateSeparator, dateSeparator != null" + "); ");
        //                return (this.dateSeparator);
        //            }

        //#if !FEATURE_CORECLR
        //            set
        //            {
        //                if (IsReadOnly)
        //                    throw new NotImplementedException(); // throw new NotImplementedException(); if (value == null)
        //                {
        //                    throw new NotImplementedException(); // throw new NotImplementedException();
        //                }
        //                Contract.EndContractBlock();
        //                ClearTokenHashTable();
        //                this.dateSeparator = value;
        //            }
        //#endif
        //        }


        public DayOfWeek FirstDayOfWeek
        {
            get
            {
                throw new NotImplementedException();
                //#if FEATURE_CORECLR
                //                if (this.firstDayOfWeek == -1)
                //                {
                //                    this.firstDayOfWeek = this.m_cultureData.IFIRSTDAYOFWEEK;
                //                }
                //#endif
                //                Contract.Assert(this.firstDayOfWeek != -1, "StarCulture.FirstDayOfWeek, firstDayOfWeek != -1");

                //                return ((DayOfWeek)this.firstDayOfWeek);
            }

            set
            {
                throw new NotImplementedException();
                //if (IsReadOnly)
                //    throw new NotImplementedException(); // throw new NotImplementedException(); if (value >= DayOfWeek.Sunday && value <= DayOfWeek.Saturday)
                //{
                //    firstDayOfWeek = (int)value;
                //}
                //else
                //{
                //    throw new NotImplementedException(); // throw new NotImplementedException();
                //}
            }
        }


        //        public CalendarWeekRule CalendarWeekRule
        //        {
        //            get
        //            {
        //#if FEATURE_CORECLR
        //                if (this.calendarWeekRule == -1)
        //                {
        //                    this.calendarWeekRule = this.m_cultureData.IFIRSTWEEKOFYEAR;
        //                }
        //#endif
        //                Contract.Assert(this.calendarWeekRule != -1, "StarCulture.CalendarWeekRule, calendarWeekRule != -1");
        //                return ((CalendarWeekRule)this.calendarWeekRule);
        //            }

        //            set
        //            {
        //                if (IsReadOnly)
        //                    throw new NotImplementedException(); // throw new NotImplementedException(); if (value >= CalendarWeekRule.FirstDay && value <= CalendarWeekRule.FirstFourDayWeek)
        //                {
        //                    calendarWeekRule = (int)value;
        //                }
        //                else
        //                {
        //                    throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
        //                        "value", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
        //                        CalendarWeekRule.FirstDay, CalendarWeekRule.FirstFourDayWeek));
        //                }
        //            }
        //        }



        public String FullStarDatePattern
        {
            get
            {
                if (fullStarDatePattern == null)
                {
                    fullStarDatePattern = LongDatePattern + " " + LongTimePattern;
                }
                return (fullStarDatePattern);
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new NotImplementedException();
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new NotImplementedException();
                }
                Contract.EndContractBlock();
                fullStarDatePattern = value;
            }
        }


        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        public String LongDatePattern
        {
            get
            {
                // Initialize our long date pattern from the 1st array value if not set
                if (this.longDatePattern == null)
                {
                    // Initialize our data
                    this.longDatePattern = this.UnclonedLongDatePatterns[0];
                }

                return this.longDatePattern;
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new NotImplementedException();
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new NotImplementedException();
                }
                Contract.EndContractBlock();

                // Remember the new string
                this.longDatePattern = value;

                // Clear the token hash table
                ClearTokenHashTable();

                // Clean up cached values that will be affected by this property.
                this.fullStarDatePattern = null;
            }
        }

        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        public String LongTimePattern
        {
            get
            {
                // Initialize our long time pattern from the 1st array value if not set
                if (this.longTimePattern == null)
                {
                    // Initialize our data
                    this.longTimePattern = this.UnclonedLongTimePatterns[0];
                }

                return this.longTimePattern;
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new NotImplementedException();
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new NotImplementedException();
                }
                Contract.EndContractBlock();

                // Remember the new string
                this.longTimePattern = value;

                // Clear the token hash table
                ClearTokenHashTable();

                // Clean up cached values that will be affected by this property.
                this.fullStarDatePattern = null;     // Full date = long date + long Time
                this.generalLongTimePattern = null;  // General long date = short date + long Time
                this.StarDateOffsetPattern = null;
            }
        }


        // Note: just to be confusing there's only 1 month day pattern, not a whole list
        //public String MonthDayPattern
        //{
        //    get
        //    {
        //        if (this.monthDayPattern == null)
        //        {
        //            Contract.Assert(ID > 0, "[StarCulture.MonthDayPattern] Expected calID > 0");
        //            this.monthDayPattern = this.MonthDay;
        //        }
        //        Contract.Assert(this.monthDayPattern != null, "StarCulture.MonthDayPattern, monthDayPattern != null");
        //        return (this.monthDayPattern);
        //    }

        //    set
        //    {
        //        if (IsReadOnly)
        //            throw new NotImplementedException(); // throw new NotImplementedException();
        //        if (value == null)
        //        {
        //            throw new NotImplementedException(); // throw new NotImplementedException();
        //        }
        //        Contract.EndContractBlock();

        //        this.monthDayPattern = value;
        //    }
        //}


        public String PMDesignator
        {
#if FEATURE_CORECLR
            [System.Security.SecuritySafeCritical]  // auto-generated
#endif
            get
            {
                //#if FEATURE_CORECLR
                if (this.pmDesignator == null)
                {
                    this.pmDesignator = this.SPM2359;
                }
                //#endif
                Contract.Assert(this.pmDesignator != null, "StarCulture.PMDesignator, pmDesignator != null");
                return (this.pmDesignator);
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new NotImplementedException();
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new NotImplementedException();
                }
                Contract.EndContractBlock();
                ClearTokenHashTable();

                pmDesignator = value;
            }

        }


        public String RFC1123Pattern
        {
            get
            {
                return (rfc1123Pattern);
            }
        }

        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        public String ShortDatePattern
        {
            get
            {
                // Initialize our short date pattern from the 1st array value if not set
                if (this.shortDatePattern == null)
                {
                    // Initialize our data
                    this.shortDatePattern = this.UnclonedShortDatePatterns[0];
                }

                return this.shortDatePattern;
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
                if (value == null)
                    throw new NotImplementedException(); // throw new ArgumentNullException("value",
                                                         //LEnvironment.GetResourceString("ArgumentNull_String"));
                Contract.EndContractBlock();

                // Remember the new string
                this.shortDatePattern = value;

                // Clear the token hash table, note that even short dates could require this
                ClearTokenHashTable();

                // Clean up cached values that will be affected by this property.
                generalLongTimePattern = null;   // General long time = short date + long time
                generalShortTimePattern = null;  // General short time = short date + short Time
                StarDateOffsetPattern = null;
            }
        }


        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        public String ShortTimePattern
        {
            get
            {
                // Initialize our short time pattern from the 1st array value if not set
                if (this.shortTimePattern == null)
                {
                    // Initialize our data
                    this.shortTimePattern = this.UnclonedShortTimePatterns[0];
                }
                return this.shortTimePattern;
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new ArgumentNullException("value",
                                                         //LEnvironment.GetResourceString("ArgumentNull_String"));
                }
                Contract.EndContractBlock();

                // Remember the new string
                this.shortTimePattern = value;

                // Clear the token hash table, note that even short times could require this
                ClearTokenHashTable();

                // Clean up cached values that will be affected by this property.
                generalShortTimePattern = null; // General short date = short date + short time.
            }
        }


        public String SortableStarDatePattern
        {
            get
            {
                return (sortableStarDatePattern);
            }
        }

        /*=================================GeneralShortTimePattern=====================
        **Property: Return the pattern for 'g' general format: shortDate + short time
        **Note: This is used by StarDateFormat.cs to get the pattern for 'g'
        **      We put this internal property here so that we can avoid doing the
        **      concatation every time somebody asks for the general format.
        ==============================================================================*/

        internal String GeneralShortTimePattern
        {
            get
            {
                if (generalShortTimePattern == null)
                {
                    generalShortTimePattern = ShortDatePattern + " " + ShortTimePattern;
                }
                return (generalShortTimePattern);
            }
        }

        /*=================================GeneralLongTimePattern=====================
        **Property: Return the pattern for 'g' general format: shortDate + Long time
        **Note: This is used by StarDateFormat.cs to get the pattern for 'g'
        **      We put this internal property here so that we can avoid doing the
        **      concatation every time somebody asks for the general format.
        ==============================================================================*/

        internal String GeneralLongTimePattern
        {
            get
            {
                if (generalLongTimePattern == null)
                {
                    generalLongTimePattern = ShortDatePattern + " " + LongTimePattern;
                }
                return (generalLongTimePattern);
            }
        }

        /*=================================StarDateOffsetPattern==========================
        **Property: Return the default pattern StarDateOffset : shortDate + long time + time zone offset
        **Note: This is used by StarDateFormat.cs to get the pattern for short Date + long time +  time zone offset
        **      We put this internal property here so that we can avoid doing the
        **      concatation every time somebody uses this form
        ==============================================================================*/

        /*=================================StarDateOffsetPattern==========================
        **Property: Return the default pattern StarDateOffset : shortDate + long time + time zone offset
        **Note: This is used by StarDateFormat.cs to get the pattern for short Date + long time +  time zone offset
        **      We put this internal property here so that we can avoid doing the
        **      concatation every time somebody uses this form
        ==============================================================================*/

        internal String StarDateOffsetPattern
        {
            get
            {
                if (StarDateOffsetPattern == null)
                {

                    StarDateOffsetPattern = ShortDatePattern + " " + LongTimePattern;

                    /* LongTimePattern might contain a "z" as part of the format string in which case we don't want to append a time zone offset */

                    bool foundZ = false;
                    bool inQuote = false;
                    char quote = '\'';
                    for (int i = 0; !foundZ && i < LongTimePattern.Length; i++)
                    {
                        switch (LongTimePattern[i])
                        {
                            case 'z':
                                /* if we aren't in a quote, we've found a z */
                                foundZ = !inQuote;
                                /* we'll fall out of the loop now because the test includes !foundZ */
                                break;
                            case '\'':
                            case '\"':
                                if (inQuote && (quote == LongTimePattern[i]))
                                {
                                    /* we were in a quote and found a matching exit quote, so we are outside a quote now */
                                    inQuote = false;
                                }
                                else if (!inQuote)
                                {
                                    quote = LongTimePattern[i];
                                    inQuote = true;
                                }
                                else
                                {
                                    /* we were in a quote and saw the other type of quote character, so we are still in a quote */
                                }
                                break;
                            case '%':
                            case '\\':
                                i++; /* skip next character that is escaped by this backslash */
                                break;
                            default:
                                break;
                        }
                    }

                    if (!foundZ)
                    {
                        StarDateOffsetPattern = StarDateOffsetPattern + " zzz";
                    }
                }
                return (StarDateOffsetPattern);
            }

            set
            {
                throw new NotImplementedException(); // throw new NotImplementedException();
            }

        }

        // Note that cultureData derives this from the long time format (unless someone's set this previously)
        // Note that this property is quite undesirable.
        // 
        //        public String TimeSeparator
        //        {
        //            get
        //            {
        ////#if FEATURE_CORECLR
        //                if (TimeSeparator == null)
        //                {
        //                    TimeSeparator = this.m_cultureData.TimeSeparator;
        //                }
        //                //#endif
        //                Contract.Assert(this.TimeSeparator != null, "StarCulture.TimeSeparator, TimeSeparator != null");
        //                return (TimeSeparator);
        //            }

        //#if !FEATURE_CORECLR
        //            set
        //            {
        //                if (IsReadOnly)
        //                    throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
        //                if (value == null)
        //                {
        //                    throw new NotImplementedException(); // throw new ArgumentNullException("value",
        //                                                         //LEnvironment.GetResourceString("ArgumentNull_String"));
        //                }
        //                Contract.EndContractBlock();
        //                ClearTokenHashTable();

        //                TimeSeparator = value;
        //            }
        //#endif
        //        }


        public String UniversalSortableStarDatePattern
        {
            get
            {
                return (universalSortableStarDatePattern);
            }
        }

        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        public String YearMonthPattern
        {
            get
            {
                // Initialize our Year/month pattern from the 1st array value if not set
                if (this.yearMonthPattern == null)
                {
                    // Initialize our data
                    this.yearMonthPattern = this.UnclonedYearMonthPatterns[0];
                }
                return this.yearMonthPattern;
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new ArgumentNullException("value",
                                                         //LEnvironment.GetResourceString("ArgumentNull_String"));
                }
                Contract.EndContractBlock();

                // Remember the new string
                this.yearMonthPattern = value;

                // Clear the token hash table, note that even short times could require this
                ClearTokenHashTable();
            }
        }

        //
        // Check if a string array contains a null value, and throw ArgumentNullException with parameter name "value"
        //
        static private void CheckNullValue(String[] values, int length)
        {
            Contract.Requires(values != null, "value != null");
            Contract.Requires(values.Length >= length);
            for (int i = 0; i < length; i++)
            {
                if (values[i] == null)
                {
                    throw new NotImplementedException(); // throw new ArgumentNullException("value",
                                                         //LEnvironment.GetResourceString("ArgumentNull_ArrayValue"));
                }
            }
        }


        //public String[] AbbreviatedDayNames
        //{
        //    get
        //    {
        //        return ((String[])internalGetAbbreviatedDayOfWeekNames().Clone());
        //    }

        //    set
        //    {
        //        if (IsReadOnly)
        //            throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
        //        if (value == null)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentNullException("value",
        //                                                 //LEnvironment.GetResourceString("ArgumentNull_Array"));
        //        }
        //        if (value.Length != 7)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 7), "value");
        //        }
        //        Contract.EndContractBlock();
        //        CheckNullValue(value, value.Length);
        //        ClearTokenHashTable();

        //        saAbbrevDayNames1 = value;
        //    }
        //}


        // Returns the string array of the one-letter day of week names.
        //[System.Runtime.InteropServices.ComVisible(false)]
        //public String[] ShortestDayNames
        //{
        //    get
        //    {
        //        return ((String[])internalGetSuperShortDayNames().Clone());
        //    }

        //    set
        //    {
        //        if (IsReadOnly)
        //            throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
        //        if (value == null)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentNullException("value",
        //                                                 //LEnvironment.GetResourceString("ArgumentNull_Array"));
        //        }
        //        if (value.Length != 7)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 7), "value");
        //        }
        //        Contract.EndContractBlock();
        //        CheckNullValue(value, value.Length);
        //        this.SuperShortDayNames = value; 
        //    }
        //}


        //public String[] DayNames
        //{
        //    get
        //    {
        //        return ((String[])internalGetDayOfWeekNames().Clone());
        //    }

        //    set
        //    {
        //        if (IsReadOnly)
        //            throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
        //        if (value == null)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentNullException("value",
        //                                                 //LEnvironment.GetResourceString("ArgumentNull_Array"));
        //        }
        //        if (value.Length != 7)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 7), "value");
        //        }
        //        Contract.EndContractBlock();
        //        CheckNullValue(value, value.Length);
        //        ClearTokenHashTable();

        //        dayNames = value;
        //    }
        //}


        //public String[] AbbreviatedMonthNames
        //{
        //    get
        //    {
        //        return ((String[])internalGetAbbreviatedMonthNames().Clone());
        //    }

        //    set
        //    {
        //        if (IsReadOnly)
        //            throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
        //        if (value == null)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentNullException("value",
        //                                                 //LEnvironment.GetResourceString("ArgumentNull_Array"));
        //        }
        //        if (value.Length != 13)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 13), "value");
        //        }
        //        Contract.EndContractBlock();
        //        CheckNullValue(value, value.Length - 1);
        //        ClearTokenHashTable();
        //        _abbreviatedMonthNames = value;
        //    }
        //}


        //public String[] MonthNames
        //{
        //    get
        //    {
        //        return ((String[])internalGetMonthNames().Clone());
        //    }

        //    set
        //    {
        //        if (IsReadOnly)
        //            throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
        //        if (value == null)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentNullException("value",
        //                                                 //LEnvironment.GetResourceString("ArgumentNull_Array"));
        //        }
        //        if (value.Length != 13)
        //        {
        //            throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 13), "value");
        //        }
        //        Contract.EndContractBlock();
        //        CheckNullValue(value, value.Length - 1);
        //        monthNames = value;
        //        ClearTokenHashTable();
        //    }
        //}

        // Whitespaces that we allow in the month names.
        // U+00a0 is non-breaking space.
        static char[] MonthSpaces = { ' ', '\u00a0' };

        internal bool HasSpacesInMonthNames
        {
            get
            {
                return (FormatFlags & StarDateFormatFlags.UseSpacesInMonthNames) != 0;
            }
        }

        internal bool HasSpacesInDayNames
        {
            get
            {
                return (FormatFlags & StarDateFormatFlags.UseSpacesInDayNames) != 0;
            }
        }


        //
        //  internalGetMonthName
        //
        // Actions: Return the month name using the specified MonthNameStyles in either abbreviated form
        //      or full form.
        // Arguments:
        //      month
        //      style           To indicate a form like regular/genitive/month name in a leap Year.
        //      abbreviated     When true, return abbreviated form.  Otherwise, return a full form.
        //  Exceptions:
        //      ArgumentOutOfRangeException When month name is invalid.
        //
        internal String internalGetMonthName(int month, MonthNameStyles style, bool abbreviated)
        {
            //
            // Right now, style is mutual exclusive, but I make the style to be flag so that
            // maybe we can combine flag if there is such a need.
            //
            String[] monthNamesArray = null;
            switch (style)
            {
                case MonthNameStyles.Genitive:
                    monthNamesArray = internalGetGenitiveMonthNames(abbreviated);
                    break;
                case MonthNameStyles.LeapYear:
                    monthNamesArray = internalGetLeapYearMonthNames(abbreviated);
                    break;
                default:
                    monthNamesArray = (abbreviated ? internalGetAbbreviatedMonthNames() : internalGetMonthNames());
                    break;
            }
            // The month range is from 1 ~ this.m_monthNames.Length
            // (actually is 13 right now for all cases)
            if ((month < 1) || (month > monthNamesArray.Length))
            {
                throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
                                                     //"month", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
                                                     //1, monthNamesArray.Length));
            }
            return (monthNamesArray[month - 1]);
        }

        //
        //  internalGetGenitiveMonthNames
        //
        //  Action: Retrieve the array which contains the month names in genitive form.
        //      If this culture does not use the gentive form, the normal month name is returned.
        //  Arguments:
        //      abbreviated     When true, return abbreviated form.  Otherwise, return a full form.
        //
        private String[] internalGetGenitiveMonthNames(bool abbreviated)
        {
            if (abbreviated)
            {
                if (this.m_genitiveAbbreviatedMonthNames == null)
                {
                    this.m_genitiveAbbreviatedMonthNames = this.AbbreviatedGenitiveMonthNames;
                    //Contract.Assert(this.m_genitiveAbbreviatedMonthNames.Length == 13,
                    //    "[StarCulture.GetGenitiveMonthNames] Expected 13 abbreviated genitive month names in a Year");
                }
                return (this.m_genitiveAbbreviatedMonthNames);
            }

            //if (this.genitiveMonthNames == null)
            //{
            //    this.genitiveMonthNames = this.GenitiveMonthNames;
            //    //Contract.Assert(this.genitiveMonthNames.Length == 13,
            //    //    "[StarCulture.GetGenitiveMonthNames] Expected 13 genitive month names in a Year");
            //}
            return (this.GenitiveMonthNames);
        }

        //
        //  internalGetLeapYearMonthNames
        //
        //  Actions: Retrieve the month names used in a leap Year.
        //      If this culture does not have different month names in a leap Year, the normal month name is returned.
        //  Agruments: None. (can use abbreviated later if needed)
        //
        internal String[] internalGetLeapYearMonthNames(bool abbreviated)
        {
            if (this.leapYearMonthNames == null)
            {
                throw new NotImplementedException();
                //Contract.Assert(ID > 0, "[StarCulture.internalGetLeapYearMonthNames] Expected StarCulture.ID > 0");
                //this.leapYearMonthNames = this.LeapYearMonthNames;
                //Contract.Assert(this.leapYearMonthNames.Length == 13,
                //    "[StarCulture.internalGetLeapYearMonthNames] Expepcted 13 leap Year month names");
            }
            return (leapYearMonthNames);
        }


        public String GetAbbreviatedDayName(DayOfWeek dayofweek)
        {

            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
                                                     //"dayofweek", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
                                                     //  DayOfWeek.Sunday, DayOfWeek.Saturday));
            }
            Contract.EndContractBlock();
            //
            // Don't call the public property AbbreviatedDayNames here since a clone is needed in that
            // property, so it will be slower.  Instead, use GetAbbreviatedDayOfWeekNames() directly.
            //
            return (internalGetAbbreviatedDayOfWeekNames()[(int)dayofweek]);
        }


        // Returns the super short day of week names for the specified day of week.
        //[System.Runtime.InteropServices.ComVisible(false)]
        //public String GetShortestDayName(DayOfWeek dayOfWeek)
        //{

        //    if ((int)dayOfWeek < 0 || (int)dayOfWeek > 6)
        //    {
        //        throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
        //                                             //"dayOfWeek", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
        //                                             //DayOfWeek.Sunday, DayOfWeek.Saturday));
        //    }
        //    Contract.EndContractBlock();
        //    //
        //    // Don't call the public property SuperShortDayNames here since a clone is needed in that
        //    // property, so it will be slower.  Instead, use internalGetSuperShortDayNames() directly.
        //    //
        //    return (SuperShortDayNames()[(int)dayOfWeek]);
        //}

        // Get all possible combination of inputs
        static private String[] GetCombinedPatterns(String[] patterns1, String[] patterns2, String connectString)
        {
            Contract.Requires(patterns1 != null);
            Contract.Requires(patterns2 != null);

            // Get array size
            String[] result = new String[patterns1.Length * patterns2.Length];

            // Counter of actual results
            int k = 0;
            for (int i = 0; i < patterns1.Length; i++)
            {
                for (int j = 0; j < patterns2.Length; j++)
                {
                    // Can't combine if null or empty
                    result[k++] = patterns1[i] + connectString + patterns2[j];
                }
            }

            // Return the combinations
            return (result);
        }


        public String[] GetAllStarDatePatterns()
        {
            List<String> results = new List<String>(DEFAULT_ALL_StarDateS_SIZE);

            for (int i = 0; i < StarDateFormat.allStandardFormats.Length; i++)
            {
                String[] strings = GetAllStarDatePatterns(StarDateFormat.allStandardFormats[i]);
                for (int j = 0; j < strings.Length; j++)
                {
                    results.Add(strings[j]);
                }
            }
            return results.ToArray();
        }


        public String[] GetAllStarDatePatterns(char format)
        {
            Contract.Ensures(Contract.Result<String[]>() != null);
            String[] result = null;

            switch (format)
            {
                case 'd':
                    result = this.AllShortDatePatterns;
                    break;
                case 'D':
                    result = this.AllLongDatePatterns;
                    break;
                case 'f':
                    result = GetCombinedPatterns(AllLongDatePatterns, AllShortTimePatterns, " ");
                    break;
                case 'F':
                case 'U':
                    result = GetCombinedPatterns(AllLongDatePatterns, AllLongTimePatterns, " ");
                    break;
                case 'g':
                    result = GetCombinedPatterns(AllShortDatePatterns, AllShortTimePatterns, " ");
                    break;
                case 'G':
                    result = GetCombinedPatterns(AllShortDatePatterns, AllLongTimePatterns, " ");
                    break;
                case 'm':
                case 'M':
                    result = new String[] { MonthDayPattern };
                    break;
                case 'o':
                case 'O':
                    result = new String[] { StarDateFormat.RoundtripFormat };
                    break;
                case 'r':
                case 'R':
                    result = new String[] { rfc1123Pattern };
                    break;
                case 's':
                    result = new String[] { sortableStarDatePattern };
                    break;
                case 't':
                    result = this.AllShortTimePatterns;
                    break;
                case 'T':
                    result = this.AllLongTimePatterns;
                    break;
                case 'u':
                    result = new String[] { UniversalSortableStarDatePattern };
                    break;
                case 'y':
                case 'Y':
                    result = this.AllYearMonthPatterns;
                    break;
                default:
                    throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Format_BadFormatSpecifier"), "format");
            }
            return (result);
        }


        public String GetDayName(DayOfWeek dayofweek)
        {
            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new ArgumentOutOfRangeException();
            }
            Contract.EndContractBlock();

            // Use the internal one so that we don't clone the array unnecessarily
            return (internalGetDayOfWeekNames()[(int)dayofweek]);
        }

        public String GetShortDayName(DayOfWeek dayofweek)
        {
            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new ArgumentOutOfRangeException();
            }
            Contract.EndContractBlock();

            // Use the internal one so that we don't clone the array unnecessarily
            return (AbbreviatedDayNames[(int)dayofweek]);
        }

        public String GetSuperShortDayName(DayOfWeek dayofweek)
        {
            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new ArgumentOutOfRangeException();
            }
            Contract.EndContractBlock();

            // Use the internal one so that we don't clone the array unnecessarily
            return (SuperShortDayNames[(int)dayofweek]);
        }



        public String GetAbbreviatedMonthName(int month)
        {
            if (month < 1 || month > 13)
            {
                throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
                                                     //"month", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
                                                     ////1, 13));
            }
            Contract.EndContractBlock();
            // Use the internal one so we don't clone the array unnecessarily
            return (internalGetAbbreviatedMonthNames()[month - 1]);
        }


        public String GetMonthName(int month)
        {
            if (month < 1 || month > 13)
            {
                throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
                                                     //"month", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
                                                     //1, 13));
            }
            Contract.EndContractBlock();
            // Use the internal one so we don't clone the array unnecessarily
            return (internalGetMonthNames()[month - 1]);
        }

        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        //
        // The resulting [] can get returned to the calling app, so clone it.
        private static string[] GetMergedPatterns(string[] patterns, string defaultPattern)
        {
            Contract.Assert(patterns != null && patterns.Length > 0,
                            "[StarCulture.GetMergedPatterns]Expected array of at least one pattern");
            Contract.Assert(defaultPattern != null,
                            "[StarCulture.GetMergedPatterns]Expected non null default string");

            // If the default happens to be the first in the list just return (a cloned) copy
            if (defaultPattern == patterns[0])
            {
                return (string[])patterns.Clone();
            }

            // We either need a bigger list, or the pattern from the list.
            int i;
            for (i = 0; i < patterns.Length; i++)
            {
                // Stop if we found it
                if (defaultPattern == patterns[i])
                    break;
            }

            // Either way we're going to need a new array
            string[] newPatterns;

            // Did we find it
            if (i < patterns.Length)
            {
                // Found it, output will be same size
                newPatterns = (string[])patterns.Clone();

                // Have to move [0] item to [i] so we can re-write default at [0]
                // (remember defaultPattern == [i] so this is OK)
                newPatterns[i] = newPatterns[0];
            }
            else
            {
                // Not found, make room for it
                newPatterns = new String[patterns.Length + 1];

                // Copy existing array
                Array.Copy(patterns, 0, newPatterns, 1, patterns.Length);
            }

            // Remember the default
            newPatterns[0] = defaultPattern;

            // Return the reconstructed list
            return newPatterns;
        }

        // Default string isn't necessarily in our string array, so get the
        // merged patterns of both
        private String[] AllYearMonthPatterns
        {
            get
            {
                return GetMergedPatterns(this.UnclonedYearMonthPatterns, this.YearMonthPattern);
            }
        }

        private String[] AllShortDatePatterns
        {
            get
            {
                return GetMergedPatterns(this.UnclonedShortDatePatterns, this.ShortDatePattern);
            }
        }

        private String[] AllShortTimePatterns
        {
            get
            {
                return GetMergedPatterns(this.UnclonedShortTimePatterns, this.ShortTimePattern);
            }
        }

        private String[] AllLongDatePatterns
        {
            get
            {
                return GetMergedPatterns(this.UnclonedLongDatePatterns, this.LongDatePattern);
            }
        }

        private String[] AllLongTimePatterns
        {
            get
            {
                return GetMergedPatterns(this.UnclonedLongTimePatterns, this.LongTimePattern);
            }
        }

        // NOTE: Clone this string array if you want to return it to user.  Otherwise, you are returning a writable cache copy.
        // This won't include default, call AllYearMonthPatterns
        private String[] UnclonedYearMonthPatterns
        {
            get
            {
                if (this.allYearMonthPatterns == null)
                {
                    //Contract.Assert(ID > 0, "[StarCulture.UnclonedYearMonthPatterns] Expected StarCulture.ID > 0");
                    this.allYearMonthPatterns = this.YearMonths();
                    //Contract.Assert(this.allYearMonthPatterns.Length > 0,
                    //    "[StarCulture.UnclonedYearMonthPatterns] Expected some Year month patterns");
                }

                return this.allYearMonthPatterns;
            }
        }


        // NOTE: Clone this string array if you want to return it to user.  Otherwise, you are returning a writable cache copy.
        // This won't include default, call AllShortDatePatterns
        private String[] UnclonedShortDatePatterns
        {
            get
            {
                if (allShortDatePatterns == null)
                {
                    Contract.Assert(ID > 0, "[StarCulture.UnclonedShortDatePatterns] Expected StarCulture.ID > 0");
                    this.allShortDatePatterns = this.ShortDates(this.ID);
                    Contract.Assert(this.allShortDatePatterns.Length > 0,
                        "[StarCulture.UnclonedShortDatePatterns] Expected some short date patterns");
                }

                return this.allShortDatePatterns;
            }
        }

        // NOTE: Clone this string array if you want to return it to user.  Otherwise, you are returning a writable cache copy.
        // This won't include default, call AllLongDatePatterns
        private String[] UnclonedLongDatePatterns
        {
            get
            {
                if (allLongDatePatterns == null)
                {
                    Contract.Assert(ID > 0, "[StarCulture.UnclonedLongDatePatterns] Expected StarCulture.ID > 0");
                    this.allLongDatePatterns = this.LongDates(this.ID);
                    Contract.Assert(this.allLongDatePatterns.Length > 0,
                        "[StarCulture.UnclonedLongDatePatterns] Expected some long date patterns");
                }

                return this.allLongDatePatterns;
            }
        }

        // NOTE: Clone this string array if you want to return it to user.  Otherwise, you are returning a writable cache copy.
        // This won't include default, call AllShortTimePatterns
        private String[] UnclonedShortTimePatterns
        {
            get
            {
                if (this.allShortTimePatterns == null)
                {
                    this.allShortTimePatterns = this.ShortTimes;
                    Contract.Assert(this.allShortTimePatterns.Length > 0,
                        "[StarCulture.UnclonedShortTimePatterns] Expected some short time patterns");
                }

                return this.allShortTimePatterns;
            }
        }

        // NOTE: Clone this string array if you want to return it to user.  Otherwise, you are returning a writable cache copy.
        // This won't include default, call AllLongTimePatterns
        private String[] UnclonedLongTimePatterns
        {
            get
            {
                if (this.allLongTimePatterns == null)
                {
                    this.allLongTimePatterns = this.LongTimes;
                    Contract.Assert(this.allLongTimePatterns.Length > 0,
                        "[StarCulture.UnclonedLongTimePatterns] Expected some long time patterns");
                }

                return this.allLongTimePatterns;
            }
        }



        //public static StarCulture ReadOnly(StarCulture sdfi)
        //{
        //    if (sdfi == null)
        //    {
        //        throw new NotImplementedException(); // throw new ArgumentNullException("sdfi",
        //                                             //LEnvironment.GetResourceString("ArgumentNull_Obj"));
        //    }
        //    Contract.EndContractBlock();
        //    if (sdfi.IsReadOnly)
        //    {
        //        return (sdfi);
        //    }
        //    StarCulture newInfo = (StarCulture)(sdfi.MemberwiseClone());
        //    // We can use the data member calendar in the setter, instead of the property StarCulture,
        //    // since the cloned copy should have the same state as the original copy.
        //    throw new NotImplementedException();
        //    //newInfo.calendar = StarCulture.ReadOnly(sdfi.StarCulture);

        //    newInfo.m_isReadOnly = true;
        //    return (newInfo);
        //}


        public bool IsReadOnly
        {
            get
            {
                return (m_isReadOnly);
            }
        }

        // Return the native name for the calendar in sdfi.StarCulture.  The native name is referred to
        // the culture used to create the sdfi.  E.g. in the following example, the native language is Japanese.
        // StarCulture sdfi = new StarCulture("ja-JP", false).StarDateFormat.StarCulture = new JapaneseCalendar();
        // String nativeName = sdfi.NativeCalendarName; // Get the Japanese name for the Japanese calendar.
        // StarCulture sdfi = new StarCulture("ja-JP", false).StarDateFormat.StarCulture = new GregorianCalendar(GregorianCalendarTypes.Localized);
        // String nativeName = sdfi.NativeCalendarName; // Get the Japanese name for the Gregorian calendar.
        //[System.Runtime.InteropServices.ComVisible(false)]
        //public String NativeCalendarName
        //{
        //    get
        //    {
        //        return this.CalendarName(StarCulture.ID);
        //    }
        //}

        //
        // Used by custom cultures and others to set the list of available formats. Note that none of them are
        // explicitly used unless someone calls GetAllStarDatePatterns and subsequently uses one of the items
        // from the list.
        //
        // Most of the format characters that can be used in GetAllStarDatePatterns are
        // not really needed since they are one of the following:
        //
        //  r/R/s/u     locale-independent constants -- cannot be changed!
        //  m/M/y/Y     fields with a single string in them -- that can be set through props directly
        //  f/F/g/G/U   derived fields based on combinations of various of the below formats
        //
        // NOTE: No special validation is done here beyond what is done when the actual respective fields
        // are used (what would be the point of disallowing here what we allow in the appropriate property?)
        //
        // WARNING: If more validation is ever done in one place, it should be done in the other.
        //

        [System.Runtime.InteropServices.ComVisible(false)]
        public void SetAllStarDatePatterns(String[] patterns, char format)
        {
            if (IsReadOnly)
                throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
            if (patterns == null)
            {
                throw new NotImplementedException(); // throw new ArgumentNullException("patterns",
                                                     //LEnvironment.GetResourceString("ArgumentNull_Array"));
            }

            if (patterns.Length == 0)
            {
                throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Arg_ArrayZeroError"), "patterns");
            }
            Contract.EndContractBlock();

            for (int i = 0; i < patterns.Length; i++)
            {
                if (patterns[i] == null)
                {
                    throw new NotImplementedException(); // throw new ArgumentNullException(//LEnvironment.GetResourceString("ArgumentNull_ArrayValue"));
                }
            }

            // Remember the patterns, and use the 1st as default
            switch (format)
            {
                case 'd':
                    this.allShortDatePatterns = patterns;
                    this.shortDatePattern = this.allShortDatePatterns[0];
                    break;

                case 'D':
                    this.allLongDatePatterns = patterns;
                    this.longDatePattern = this.allLongDatePatterns[0];
                    break;

                case 't':
                    this.allShortTimePatterns = patterns;
                    this.shortTimePattern = this.allShortTimePatterns[0];
                    break;

                case 'T':
                    this.allLongTimePatterns = patterns;
                    this.longTimePattern = this.allLongTimePatterns[0];
                    break;

                case 'y':
                case 'Y':
                    this.allYearMonthPatterns = patterns;
                    this.yearMonthPattern = this.allYearMonthPatterns[0];
                    break;

                default:
                    throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Format_BadFormatSpecifier"), "format");
            }

            // Clear the token hash table, note that even short dates could require this
            ClearTokenHashTable();

            return;
        }

        [System.Runtime.InteropServices.ComVisible(false)]
        public String[] AbbreviatedMonthGenitiveNames
        {
            get
            {
                return ((String[])internalGetGenitiveMonthNames(true).Clone());
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new ArgumentNullException("value",
                                                         //LEnvironment.GetResourceString("ArgumentNull_Array"));
                }
                if (value.Length != 13)
                {
                    throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 13), "value");
                }
                Contract.EndContractBlock();
                CheckNullValue(value, value.Length - 1);
                ClearTokenHashTable();
                this.m_genitiveAbbreviatedMonthNames = value;
            }
        }

        [System.Runtime.InteropServices.ComVisible(false)]
        public String[] MonthGenitiveNames
        {
            get
            {
                return ((String[])internalGetGenitiveMonthNames(false).Clone());
            }

            set
            {
                if (IsReadOnly)
                    throw new NotImplementedException(); // throw new InvalidOperationException(//LEnvironment.GetResourceString("InvalidOperation_ReadOnly"));
                if (value == null)
                {
                    throw new NotImplementedException(); // throw new ArgumentNullException("value",
                                                         //LEnvironment.GetResourceString("ArgumentNull_Array"));
                }
                if (value.Length != 13)
                {
                    throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 13), "value");
                }
                Contract.EndContractBlock();
                CheckNullValue(value, value.Length - 1);
                genitiveMonthNames = value;
                ClearTokenHashTable();
            }
        }

        //
        // Positive TimeSpan Pattern
        //
        [NonSerialized]
        private string m_fullTimeSpanPositivePattern;
        internal String FullTimeSpanPositivePattern
        {
            get
            {
                if (m_fullTimeSpanPositivePattern == null)
                {
                    StarCulture cultureDataWithoutUserOverrides;
                    if (UseUserOverride)
                        cultureDataWithoutUserOverrides = StarCulture.GetCultureData(CultureName, false);
                    else
                        cultureDataWithoutUserOverrides = this;
                    String decimalSeparator = new NumberFormatInfo(cultureDataWithoutUserOverrides).NumberDecimalSeparator;

                    m_fullTimeSpanPositivePattern = "d':'h':'mm':'ss'" + decimalSeparator + "'FFFFFFF";
                }
                return m_fullTimeSpanPositivePattern;
            }
        }

        //
        // Negative TimeSpan Pattern
        //
        [NonSerialized]
        private string m_fullTimeSpanNegativePattern;
        internal String FullTimeSpanNegativePattern
        {
            get
            {
                if (m_fullTimeSpanNegativePattern == null)
                    m_fullTimeSpanNegativePattern = "'-'" + FullTimeSpanPositivePattern;
                return m_fullTimeSpanNegativePattern;
            }
        }

        //
        // Get suitable CompareInfo from current sdfi object.
        //
        //internal CompareInfo CompareInfo
        //{
        //    get
        //    {
        //        if (m_compareInfo == null)
        //        {
        //            // We use the regular GetCompareInfo here to make sure the created CompareInfo object is stored in the
        //            // CompareInfo cache. otherwise we would just create CompareInfo using m_cultureData.
        //            m_compareInfo = CompareInfo.GetCompareInfo(SCOMPAREINFO);
        //        }

        //        return m_compareInfo;
        //    }
        //}


        internal const StarDateStyles InvalidStarDateStyles = ~(StarDateStyles.AllowLeadingWhite | StarDateStyles.AllowTrailingWhite
                                                               | StarDateStyles.AllowInnerWhite | StarDateStyles.NoCurrentDateDefault
                                                               | StarDateStyles.AdjustToUniversal | StarDateStyles.AssumeLocal
                                                               | StarDateStyles.AssumeUniversal | StarDateStyles.RoundtripKind);

        internal static void ValidateStyles(StarDateStyles style, String parameterName)
        {
            if ((style & InvalidStarDateStyles) != 0)
            {
                throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidStarDateStyles"), parameterName);
            }
            if (((style & (StarDateStyles.AssumeLocal)) != 0) && ((style & (StarDateStyles.AssumeUniversal)) != 0))
            {
                throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_ConflictingStarDateStyles"), parameterName);
            }
            Contract.EndContractBlock();
            if (((style & StarDateStyles.RoundtripKind) != 0)
                && ((style & (StarDateStyles.AssumeLocal | StarDateStyles.AssumeUniversal | StarDateStyles.AdjustToUniversal)) != 0))
            {
                throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_ConflictingStarDateRoundtripStyles"), parameterName);
            }
        }

        //
        // Actions: Return the internal flag used in formatting and parsing.
        //  The flag can be used to indicate things like if genitive forms is used in this sdfi, or if leap Year gets different month names.
        //
        internal StarDateFormatFlags FormatFlags
        {
            get
            {
                //throw new NotImplementedException();
                if (formatFlags == StarDateFormatFlags.NotInitialized)
                {
                    // Build the format flags from the data in this sdfi
                    //formatFlags = StarDateFormatFlags.None;
                    //formatFlags |= (StarDateFormatFlags)StarDateFormatInfoScanner.GetFormatFlagGenitiveMonth(
                    //    MonthNames, internalGetGenitiveMonthNames(false), AbbreviatedMonthNames, internalGetGenitiveMonthNames(true));
                    //formatFlags |= (StarDateFormatFlags)StarDateFormatInfoScanner.GetFormatFlagUseSpaceInMonthNames(
                    //    MonthNames, internalGetGenitiveMonthNames(false), AbbreviatedMonthNames, internalGetGenitiveMonthNames(true));
                    //formatFlags |= (StarDateFormatFlags)StarDateFormatInfoScanner.GetFormatFlagUseSpaceInDayNames(DayNames, AbbreviatedDayNames);
                    //formatFlags |= (StarDateFormatFlags)StarDateFormatInfoScanner.GetFormatFlagUseHebrewCalendar((int)StarCulture.ID);
                }
                return (formatFlags);
            }
        }

        //internal Boolean HasForceTwoDigitYears
        //{
        //    get
        //    {
        //        switch 
        //        {
        //            /*  */
        //            // If is y/yy, do not get (Year % 100). "y" will print
        //            // Year without leading zero.  "yy" will print Year with two-digit in leading zero.
        //            // If pattern is yyy/yyyy/..., print Year value with two-digit in leading zero.
        //            // So Year 5 is "05", and Year 125 is "125".
        //            // The reason for not doing (Year % 100) is for Taiwan calendar.
        //            // If Year 125, then output 125 and not 25.
        //            // Note: OS uses "yyyy" for Taiwan calendar by default.
        //            case (StarCulture.CAL_JAPAN):
        //            case (StarCulture.CAL_TAIWAN):
        //                return true;
        //        }
        //        return false;
        //    }
        //}

        // Returns whether the YearMonthAdjustment function has any fix-up work to do for this culture/calendar.
        internal Boolean HasYearMonthAdjustment
        {
            get
            {
                return ((FormatFlags & StarDateFormatFlags.UseHebrewRule) != 0);
            }
        }

        //public static StarCulture GregorianCalendar { get; }
        //public object AppContextSwitches { get; private set; }
        public bool HasForceTwoDigitYears { get; internal set; }

        //public StarCulture CultureData { get => CultureData1; set => CultureData1 = value; }
        //public StarCulture CultureData1
        //{
        //    get
        //    {
        //        if (m_cultureData == null)
        //        {
        //            m_cultureData = StarCulture.CurrentCulture;
        //        }
        //        return m_cultureData;
        //    }

        //    set
        //    {
        //        m_cultureData = value;
        //    }
        //}

        public string GetDateSeparator()
        {
            if (dateSeparator1 == null)
            {
                dateSeparator1 = "-";
            }
            return dateSeparator1;
        }
        //public StarCulture CultureData { get => CultureData1; set => CultureData1 = value; }
        //public StarCulture CultureData1
        //{
        //    get
        //    {
        //        if (m_cultureData == null)
        //        {
        //            m_cultureData = StarCulture.CurrentCulture;
        //        }
        //        return m_cultureData;
        //    }

        //    set
        //    {
        //        m_cultureData = value;
        //    }
        //}

        internal void SetDateSeparator(string value)
        {
            dateSeparator1 = value;
        }

        // This is a callback that the parser can make back into the sdfi to let it fiddle with special
        // cases associated with that culture or calendar. Currently this only has special cases for
        // the Hebrew calendar, but this could be extended to other cultures.
        //
        // The return value is whether the Year and month are actually valid for this calendar.
        //internal Boolean YearMonthAdjustment(ref int Year, ref int month, Boolean parsedMonthName)
        //{
        //    if ((FormatFlags & StarDateFormatFlags.UseHebrewRule) != 0)
        //    {

        //        // Special rules to fix up the Hebrew Year/month

        //        // When formatting, we only format up to the hundred digit of the Hebrew Year, although Hebrew Year is now over 5000.
        //        // E.g. if the Year is 5763, we only format as 763.
        //        if (Year < 1000)
        //        {
        //            Year += 5000;
        //        }

        //        // Because we need to calculate leap Year, we should fall out now for an invalid Year.
        //        if (Year < Calendar.GetYear(Calendar.MinSupportedStarDate) || Year > Calendar.GetYear(Calendar.MaxSupportedStarDate))
        //        {
        //            return false;
        //        }

        //        // To handle leap months, the set of month names in the symbol table does not always correspond to the numbers.
        //        // For non-leap years, month 7 (Adar Bet) is not present, so we need to make using this month invalid and
        //        // shuffle the other months down.
        //        if (parsedMonthName)
        //        {
        //            if (!Calendar.IsLeapYear(Year))
        //            {
        //                if (month >= 8)
        //                {
        //                    month--;
        //                }
        //                else if (month == 7)
        //                {
        //                    return false;
        //                }
        //            }
        //        }
        //    }
        //    return true;
        //}

        //
        // StarCulture tokenizer.  This is used by StarDate.Parse() to break input string into tokens.
        //
        [NonSerialized]
        private TokenHashValue[] m_sdfiTokenHash;
        private const int SECOND_PRIME = 197;
        private const String dateSeparatorOrTimeZoneOffset = "-";
        private const String invariantDateSeparator = "/";
        private const String invariantTimeSeparator = ":";

        //
        // Common Ignorable Symbols
        //
        internal const String IgnorablePeriod = ".";
        internal const String IgnorableComma = ",";

        //
        // Year/Month/Day suffixes
        //
        internal const String CJKYearSuff = "\u5e74";
        internal const String CJKMonthSuff = "\u6708";
        internal const String CJKDaySuff = "\u65e5";

        internal const String KoreanYearSuff = "\ub144";
        internal const String KoreanMonthSuff = "\uc6d4";
        internal const String KoreanDaySuff = "\uc77c";

        internal const String KoreanHourSuff = "\uc2dc";
        internal const String KoreanMinuteSuff = "\ubd84";
        internal const String KoreanSecondSuff = "\ucd08";

        internal const String CJKHourSuff = "\u6642";
        internal const String ChineseHourSuff = "\u65f6";

        internal const String CJKMinuteSuff = "\u5206";
        internal const String CJKSecondSuff = "\u79d2";

        internal const string JapaneseEraStart = "\u5143";

        internal const String LocalTimeMark = "T";

        internal const String KoreanLangName = "ko";
        internal const String JapaneseLangName = "ja";
        internal const String EnglishLangName = "en";
        private const int V1 = 666;
        private const int V = V1;

        //
        // Create a Japanese sdfi which uses JapaneseCalendar.  This is used to parse
        // date string with Japanese era name correctly even when the supplied sdfi
        // does not use Japanese calendar.
        // The created instance is stored in global s_jajpsdfi.
        //
        //internal static StarCulture GetJapaneseCalendarsdfi()
        //{
        //    StarCulture temp = s_jajpsdfi;
        //    if (temp == null)
        //    {
        //        temp = new StarCulture("ja-JP", false).StarDateFormat;
        //        temp.StarCulture = JapaneseCalendar.GetDefaultInstance();
        //        s_jajpsdfi = temp;
        //    }
        //    return (temp);
        //}

        /* 





        // */
        //internal static StarCulture GetTaiwanCalendarsdfi()
        //{
        //    StarCulture temp = s_zhtwsdfi;
        //    if (temp == null)
        //    {
        //        temp = new StarCulture("zh-TW", false).StarDateFormat;
        //        temp.StarCulture = TaiwanCalendar.GetDefaultInstance();
        //        s_zhtwsdfi = temp;
        //    }
        //    return (temp);
        //}


        // sdfi properties should call this when the setter are called.
        private void ClearTokenHashTable()
        {
            m_sdfiTokenHash = null;
            formatFlags = StarDateFormatFlags.NotInitialized;
        }

        [System.Security.SecurityCritical]  // auto-generated
        //internal TokenHashValue[] CreateTokenHashTable()
        //{
        //    TokenHashValue[] temp = m_sdfiTokenHash;
        //    if (temp == null)
        //    {
        //        temp = new TokenHashValue[TOKEN_HASH_SIZE];

        //        bool koreanLanguage = LanguageName.Equals(KoreanLangName);

        //        string sep = this.TimeSeparator.Trim();
        //        if (IgnorableComma != sep) InsertHash(temp, IgnorableComma, TokenType.IgnorableSymbol, 0);
        //        if (IgnorablePeriod != sep) InsertHash(temp, IgnorablePeriod, TokenType.IgnorableSymbol, 0);

        //        if (KoreanHourSuff != sep && CJKHourSuff != sep && ChineseHourSuff != sep)
        //        {
        //            //
        //            // On the Macintosh, the default TimeSeparator is identical to the KoreanHourSuff, CJKHourSuff, or ChineseHourSuff for some cultures like
        //            // ja-JP and ko-KR.  In these cases having the same symbol inserted into the hash table with multiple TokenTypes causes undesirable
        //            // StarDate.Parse behavior.  For instance, the StarCulture.Tokenize() method might return SEP_DateOrOffset for KoreanHourSuff
        //            // instead of SEP_HourSuff.
        //            //
        //            InsertHash(temp, this.TimeSeparator, TokenType.SEP_Time, 0);
        //        }

        //        InsertHash(temp, this.AMDesignator, TokenType.SEP_Am | TokenType.Am, 0);
        //        InsertHash(temp, this.PMDesignator, TokenType.SEP_Pm | TokenType.Pm, 1);

        //        // 
        //        if (LanguageName.Equals("sq"))
        //        {
        //            // Albanian allows time formats like "12:00.PD"
        //            InsertHash(temp, IgnorablePeriod + this.AMDesignator, TokenType.SEP_Am | TokenType.Am, 0);
        //            InsertHash(temp, IgnorablePeriod + this.PMDesignator, TokenType.SEP_Pm | TokenType.Pm, 1);
        //        }

        //        // CJK suffix
        //        InsertHash(temp, CJKYearSuff, TokenType.SEP_YearSuff, 0);
        //        InsertHash(temp, KoreanYearSuff, TokenType.SEP_YearSuff, 0);
        //        InsertHash(temp, CJKMonthSuff, TokenType.SEP_MonthSuff, 0);
        //        InsertHash(temp, KoreanMonthSuff, TokenType.SEP_MonthSuff, 0);
        //        InsertHash(temp, CJKDaySuff, TokenType.SEP_DaySuff, 0);
        //        InsertHash(temp, KoreanDaySuff, TokenType.SEP_DaySuff, 0);

        //        InsertHash(temp, CJKHourSuff, TokenType.SEP_HourSuff, 0);
        //        InsertHash(temp, ChineseHourSuff, TokenType.SEP_HourSuff, 0);
        //        InsertHash(temp, CJKMinuteSuff, TokenType.SEP_MinuteSuff, 0);
        //        InsertHash(temp, CJKSecondSuff, TokenType.SEP_SecondSuff, 0);

        //        if (!AppContextSwitches.EnforceLegacyJapaneseDateParsing && StarCulture.ID == StarCulture.CAL_JAPAN)
        //        {
        //            // We need to support parsing the dates has the start of era symbol which means it is Year 1 in the era.
        //            // The start of era symbol has to be followed by the Year symbol suffix, otherwise it would be invalid date.
        //            InsertHash(temp, JapaneseEraStart, TokenType.YearNumberToken, 1);
        //            InsertHash(temp, "(", TokenType.IgnorableSymbol, 0);
        //            InsertHash(temp, ")", TokenType.IgnorableSymbol, 0);
        //        }

        //        // 
        //        if (koreanLanguage)
        //        {
        //            // Korean suffix
        //            InsertHash(temp, KoreanHourSuff, TokenType.SEP_HourSuff, 0);
        //            InsertHash(temp, KoreanMinuteSuff, TokenType.SEP_MinuteSuff, 0);
        //            InsertHash(temp, KoreanSecondSuff, TokenType.SEP_SecondSuff, 0);
        //        }

        //        if (LanguageName.Equals("ky"))
        //        {
        //            // For some cultures, the date separator works more like a comma, being allowed before or after any date part
        //            InsertHash(temp, dateSeparatorOrTimeZoneOffset, TokenType.IgnorableSymbol, 0);
        //        }
        //        else
        //        {
        //            InsertHash(temp, dateSeparatorOrTimeZoneOffset, TokenType.SEP_DateOrOffset, 0);
        //        }

        //        String[] dateWords = null;
        //        StarDateFormatInfoScanner scanner = null;

        //        // We need to rescan the date words since we're always synthetic
        //        scanner = new StarDateFormatInfoScanner();
        //        // Enumarate all LongDatePatterns, and get the DateWords and scan for month postfix.
        //        // The only reason they're being assigned to m_dateWords is for Whidbey Deserialization
        //        m_dateWords = dateWords = scanner.GetDateWordsOfsdfi(this);
        //        // Ensure the formatflags is initialized.
        //        StarDateFormatFlags flag = FormatFlags;

        //        // For some cultures, the date separator works more like a comma, being allowed before or after any date part.
        //        // In these cultures, we do not use normal date separator since we disallow date separator after a date terminal state.
        //        // This is determined in StarDateFormatInfoScanner.  Use this flag to determine if we should treat date separator as ignorable symbol.
        //        bool useDateSepAsIgnorableSymbol = false;

        //        String monthPostfix = null;
        //        if (dateWords != null)
        //        {
        //            // There are DateWords.  It could be a real date word (such as "de"), or a monthPostfix.
        //            // The monthPostfix starts with '\xfffe' (MonthPostfixChar), followed by the real monthPostfix.
        //            for (int i = 0; i < dateWords.Length; i++)
        //            {
        //                switch (dateWords[i][0])
        //                {
        //                    // This is a month postfix
        //                    case StarDateFormatInfoScanner.MonthPostfixChar:
        //                        // Get the real month postfix.
        //                        monthPostfix = dateWords[i].Substring(1);
        //                        // Add the month name + postfix into the token.
        //                        AddMonthNames(temp, monthPostfix);
        //                        break;
        //                    case StarDateFormatInfoScanner.IgnorableSymbolChar:
        //                        String symbol = dateWords[i].Substring(1);
        //                        InsertHash(temp, symbol, TokenType.IgnorableSymbol, 0);
        //                        if (this.GetDateSeparator.Trim(null).Equals(symbol))
        //                        {
        //                            // The date separator is the same as the ingorable symbol.
        //                            useDateSepAsIgnorableSymbol = true;
        //                        }
        //                        break;
        //                    default:
        //                        InsertHash(temp, dateWords[i], TokenType.DateWordToken, 0);
        //                        // 
        //                        if (LanguageName.Equals("eu"))
        //                        {
        //                            // Basque has date words with leading dots
        //                            InsertHash(temp, IgnorablePeriod + dateWords[i], TokenType.DateWordToken, 0);
        //                        }
        //                        break;
        //                }
        //            }
        //        }

        //        if (!useDateSepAsIgnorableSymbol)
        //        {
        //            // Use the normal date separator.
        //            InsertHash(temp, this.GetDateSeparator, TokenType.SEP_Date, 0);
        //        }
        //        // Add the regular month names.
        //        AddMonthNames(temp, null);

        //        // Add the abbreviated month names.
        //        for (int i = 1; i <= 13; i++)
        //        {
        //            InsertHash(temp, GetAbbreviatedMonthName(i), TokenType.MonthToken, i);
        //        }


        //        if ((FormatFlags & StarDateFormatFlags.UseGenitiveMonth) != 0)
        //        {
        //            for (int i = 1; i <= 13; i++)
        //            {
        //                String str;
        //                str = internalGetMonthName(i, MonthNameStyles.Genitive, false);
        //                InsertHash(temp, str, TokenType.MonthToken, i);
        //            }
        //        }

        //        if ((FormatFlags & StarDateFormatFlags.UseLeapYearMonth) != 0)
        //        {
        //            for (int i = 1; i <= 13; i++)
        //            {
        //                String str;
        //                str = internalGetMonthName(i, MonthNameStyles.LeapYear, false);
        //                InsertHash(temp, str, TokenType.MonthToken, i);
        //            }
        //        }

        //        for (int i = 0; i < 7; i++)
        //        {
        //            //String str = GetDayOfWeekNames()[i];
        //            // We have to call public methods here to work with inherited sdfi.
        //            String str = GetDayName((DayOfWeek)i);
        //            InsertHash(temp, str, TokenType.DayOfWeekToken, i);

        //            str = GetAbbreviatedDayName((DayOfWeek)i);
        //            InsertHash(temp, str, TokenType.DayOfWeekToken, i);

        //        }

        //        int[] eras = calendar.Eras;
        //        for (int i = 1; i <= eras.Length; i++)
        //        {
        //            InsertHash(temp, GetEraName(i), TokenType.EraToken, i);
        //            InsertHash(temp, GetAbbreviatedEraName(i), TokenType.EraToken, i);
        //        }

        //        // 
        //        if (LanguageName.Equals(JapaneseLangName))
        //        {
        //            // Japanese allows day of week forms like: "(Tue)"
        //            for (int i = 0; i < 7; i++)
        //            {
        //                String specialDayOfWeek = "(" + GetAbbreviatedDayName((DayOfWeek)i) + ")";
        //                InsertHash(temp, specialDayOfWeek, TokenType.DayOfWeekToken, i);
        //            }
        //            if (this.StarCulture.GetType() != typeof(JapaneseCalendar))
        //            {
        //                // Special case for Japanese.  If this is a Japanese sdfi, and the calendar is not Japanese calendar,
        //                // we will check Japanese Era name as well when the calendar is Gregorian.
        //                StarCulture jasdfi = GetJapaneseCalendarsdfi();
        //                for (int i = 1; i <= jasdfi.StarCulture.Eras.Length; i++)
        //                {
        //                    InsertHash(temp, jasdfi.GetEraName(i), TokenType.JapaneseEraToken, i);
        //                    InsertHash(temp, jasdfi.GetAbbreviatedEraName(i), TokenType.JapaneseEraToken, i);
        //                    // m_abbrevEnglishEraNames[0] contains the name for era 1, so the token value is i+1.
        //                    InsertHash(temp, jasdfi.AbbreviatedEnglishEraNames[i - 1], TokenType.JapaneseEraToken, i);
        //                }
        //            }
        //        }
        //        // 
        //        else if (CultureName.Equals("zh-TW"))
        //        {
        //            StarCulture twsdfi = GetTaiwanCalendarsdfi();
        //            for (int i = 1; i <= twsdfi.StarCulture.Eras.Length; i++)
        //            {
        //                if (twsdfi.GetEraName(i).Length > 0)
        //                {
        //                    InsertHash(temp, twsdfi.GetEraName(i), TokenType.TEraToken, i);
        //                }
        //            }
        //        }

        //        InsertHash(temp, InvariantCulture.AMDesignator, TokenType.SEP_Am | TokenType.Am, 0);
        //        InsertHash(temp, InvariantCulture.PMDesignator, TokenType.SEP_Pm | TokenType.Pm, 1);

        //        // Add invariant month names and day names.
        //        for (int i = 1; i <= 12; i++)
        //        {
        //            String str;
        //            // We have to call public methods here to work with inherited sdfi.
        //            // Insert the month name first, so that they are at the front of abbrevaited
        //            // month names.
        //            str = InvariantCulture.GetMonthName(i);
        //            InsertHash(temp, str, TokenType.MonthToken, i);
        //            str = InvariantCulture.GetAbbreviatedMonthName(i);
        //            InsertHash(temp, str, TokenType.MonthToken, i);
        //        }

        //        for (int i = 0; i < 7; i++)
        //        {
        //            // We have to call public methods here to work with inherited sdfi.
        //            String str = InvariantCulture.GetDayName((DayOfWeek)i);
        //            InsertHash(temp, str, TokenType.DayOfWeekToken, i);

        //            str = InvariantCulture.GetAbbreviatedDayName((DayOfWeek)i);
        //            InsertHash(temp, str, TokenType.DayOfWeekToken, i);

        //        }

        //        for (int i = 0; i < AbbreviatedEnglishEraNames.Length; i++)
        //        {
        //            // m_abbrevEnglishEraNames[0] contains the name for era 1, so the token value is i+1.
        //            InsertHash(temp, AbbreviatedEnglishEraNames[i], TokenType.EraToken, i + 1);
        //        }

        //        InsertHash(temp, LocalTimeMark, TokenType.SEP_LocalTimeMark, 0);
        //        InsertHash(temp, StarDateParse.GMTName, TokenType.TimeZoneToken, 0);
        //        InsertHash(temp, StarDateParse.ZuluName, TokenType.TimeZoneToken, 0);

        //        InsertHash(temp, invariantDateSeparator, TokenType.SEP_Date, 0);
        //        InsertHash(temp, invariantTimeSeparator, TokenType.SEP_Time, 0);

        //        m_sdfiTokenHash = temp;
        //    }
        //    return (temp);
        //}

        private void InsertHash(TokenHashValue[] temp, string aMDesignator, object p, int v)
        {
            throw new NotImplementedException();
        }

        //private void AddMonthNames(TokenHashValue[] temp, String monthPostfix)
        //{
        //    for (int i = 1; i <= 13; i++)
        //    {
        //        String str;
        //        //str = internalGetMonthName(i, MonthNameStyles.Regular, false);
        //        // We have to call public methods here to work with inherited sdfi.
        //        // Insert the month name first, so that they are at the front of abbrevaited
        //        // month names.
        //        str = GetMonthName(i);
        //        if (str.Length > 0)
        //        {
        //            if (monthPostfix != null)
        //            {
        //                // Insert the month name with the postfix first, so it can be matched first.
        //                InsertHash(temp, str + monthPostfix, TokenType.MonthToken, i);
        //            }
        //            else
        //            {
        //                InsertHash(temp, str, TokenType.MonthToken, i);
        //            }
        //        }
        //        str = GetAbbreviatedMonthName(i);
        //        InsertHash(temp, str, TokenType.MonthToken, i);
        //    }

        //}

        ////////////////////////////////////////////////////////////////////////
        //
        // Actions:
        // Try to parse the current word to see if it is a Hebrew number.
        // Tokens will be updated accordingly.
        // This is called by the Lexer of StarDate.Parse().
        //
        // Unlike most of the functions in this class, the return value indicates
        // whether or not it started to parse. The badFormat parameter indicates
        // if parsing began, but the format was bad.
        //
        ////////////////////////////////////////////////////////////////////////

        //private static bool TryParseHebrewNumber(
        //    ref __DTString str,
        //    out Boolean badFormat,
        //    out int number)
        //{

        //    number = -1;
        //    badFormat = false;

        //    int i = str.Index;
        //    if (!HebrewNumber.IsDigit(str.Value[i]))
        //    {
        //        // If the current character is not a Hebrew digit, just return false.
        //        // There is no chance that we can parse a valid Hebrew number from here.
        //        return (false);
        //    }
        //    // The current character is a Hebrew digit.  Try to parse this word as a Hebrew number.
        //    HebrewNumberParsingContext context = new HebrewNumberParsingContext(0);
        //    HebrewNumberParsingState state;

        //    do
        //    {
        //        state = HebrewNumber.ParseByChar(str.Value[i++], ref context);
        //        switch (state)
        //        {
        //            case HebrewNumberParsingState.InvalidHebrewNumber:    // Not a valid Hebrew number.
        //            case HebrewNumberParsingState.NotHebrewDigit:         // The current character is not a Hebrew digit character.
        //                // Break out so that we don't continue to try parse this as a Hebrew number.
        //                return (false);
        //        }
        //    } while (i < str.Value.Length && (state != HebrewNumberParsingState.FoundEndOfHebrewNumber));

        //    // When we are here, we are either at the end of the string, or we find a valid Hebrew number.
        //    Contract.Assert(state == HebrewNumberParsingState.ContinueParsing || state == HebrewNumberParsingState.FoundEndOfHebrewNumber,
        //        "Invalid returned state from HebrewNumber.ParseByChar()");

        //    if (state != HebrewNumberParsingState.FoundEndOfHebrewNumber)
        //    {
        //        // We reach end of the string but we can't find a terminal state in parsing Hebrew number.
        //        return (false);
        //    }

        //    // We have found a valid Hebrew number.  Update the index.
        //    str.Advance(i - str.Index);

        //    // Get the final Hebrew number value from the HebrewNumberParsingContext.
        //    number = context.result;

        //    return (true);
        //}

        private static bool IsHebrewChar(char ch)
        {
            return (ch >= '\x0590' && ch <= '\x05ff');
        }

        //[MethodImplAttribute(MethodImplOptions.AggressiveInlining)]
        //private bool IsAllowedJapaneseTokenFollowedByNonSpaceLetter(string tokenString, char nextCh)
        //{
        //    // Allow the parser to recognize the case when having some date part followed by JapaneseEraStart "\u5143"
        //    // without spaces in between. e.g. Era name followed by \u5143 in the date formats ggy.
        //    // Also, allow recognizing the Year suffix symbol "\u5e74" followed the JapaneseEraStart "\u5143"
        //    if (!AppContextSwitches.EnforceLegacyJapaneseDateParsing && StarCulture.ID == StarCulture.CAL_JAPAN &&
        //        (
        //            // something like ggy, era followed by Year and the Year is specified using the JapaneseEraStart "\u5143"
        //            nextCh == JapaneseEraStart[0] ||
        //            // JapaneseEraStart followed by Year suffix "\u5143"
        //            (tokenString == JapaneseEraStart && nextCh == CJKYearSuff[0])
        //        ))
        //    {
        //        return true;
        //    }

        //    return false;
        //}

        [System.Security.SecurityCritical]  // auto-generated
        //internal bool Tokenize(TokenType TokenMask, out TokenType tokenType, out int tokenValue, ref __DTString str)
        //{
        //    tokenType = TokenType.UnknownToken;
        //    tokenValue = 0;

        //    TokenHashValue value;
        //    Contract.Assert(str.Index < str.Value.Length, "StarCulture.Tokenize(): start < value.Length");

        //    char ch = str.m_current;
        //    bool isLetter = Char.IsLetter(ch);
        //    if (isLetter)
        //    {
        //        ch = Char.ToLower(ch, this.Culture);
        //        if (IsHebrewChar(ch) && TokenMask == TokenType.RegularTokenMask)
        //        {
        //            bool badFormat;
        //            if (TryParseHebrewNumber(ref str, out badFormat, out tokenValue))
        //            {
        //                if (badFormat)
        //                {
        //                    tokenType = TokenType.UnknownToken;
        //                    return (false);
        //                }
        //                // This is a Hebrew number.
        //                // Do nothing here.  TryParseHebrewNumber() will update token accordingly.
        //                tokenType = TokenType.HebrewNumber;
        //                return (true);
        //            }
        //        }
        //    }


        //    int hashcode = ch % TOKEN_HASH_SIZE;
        //    int hashProbe = 1 + ch % SECOND_PRIME;
        //    int remaining = str.len - str.Index;
        //    int i = 0;

        //    TokenHashValue[] hashTable = m_sdfiTokenHash;
        //    if (hashTable == null)
        //    {
        //        hashTable = CreateTokenHashTable();
        //    }
        //    do
        //    {
        //        value = hashTable[hashcode];
        //        if (value == null)
        //        {
        //            // Not found.
        //            break;
        //        }
        //        // Check this value has the right category (regular token or separator token) that we are looking for.
        //        if (((int)value.tokenType & (int)TokenMask) > 0 && value.tokenString.Length <= remaining)
        //        {
        //            if (String.Compare(str.Value, str.Index, value.tokenString, 0, value.tokenString.Length, this.Culture, CompareOptions.IgnoreCase) == 0)
        //            {
        //                if (isLetter)
        //                {
        //                    // If this token starts with a letter, make sure that we won't allow partial match.  So you can't tokenize "MarchWed" separately.
        //                    int nextCharIndex;
        //                    if ((nextCharIndex = str.Index + value.tokenString.Length) < str.len)
        //                    {
        //                        // Check word boundary.  The next character should NOT be a letter.
        //                        char nextCh = str.Value[nextCharIndex];
        //                        if (Char.IsLetter(nextCh))
        //                        {
        //                            if (!IsAllowedJapaneseTokenFollowedByNonSpaceLetter(value.tokenString, nextCh))
        //                                return (false);
        //                        }
        //                    }
        //                }
        //                tokenType = value.tokenType & TokenMask;
        //                tokenValue = value.tokenValue;
        //                str.Advance(value.tokenString.Length);
        //                return (true);
        //            }
        //            else if (value.tokenType == TokenType.MonthToken && HasSpacesInMonthNames)
        //            {
        //                // For month token, we will match the month names which have spaces.
        //                int matchStrLen = 0;
        //                if (str.MatchSpecifiedWords(value.tokenString, true, ref matchStrLen))
        //                {
        //                    tokenType = value.tokenType & TokenMask;
        //                    tokenValue = value.tokenValue;
        //                    str.Advance(matchStrLen);
        //                    return (true);
        //                }
        //            }
        //            else if (value.tokenType == TokenType.DayOfWeekToken && HasSpacesInDayNames)
        //            {
        //                // For month token, we will match the month names which have spaces.
        //                int matchStrLen = 0;
        //                if (str.MatchSpecifiedWords(value.tokenString, true, ref matchStrLen))
        //                {
        //                    tokenType = value.tokenType & TokenMask;
        //                    tokenValue = value.tokenValue;
        //                    str.Advance(matchStrLen);
        //                    return (true);
        //                }
        //            }
        //        }
        //        i++;
        //        hashcode += hashProbe;
        //        if (hashcode >= TOKEN_HASH_SIZE) hashcode -= TOKEN_HASH_SIZE;
        //    } while (i < TOKEN_HASH_SIZE);

        //    return (false);
        //}

        //void InsertAtCurrentHashNode(TokenHashValue[] hashTable, String str, char ch, TokenType tokenType, int tokenValue, int pos, int hashcode, int hashProbe)
        //{
        //    // Remember the current slot.
        //    TokenHashValue previousNode = hashTable[hashcode];

        //    //// //////Console.WriteLine("   Insert Key: {0} in {1}", str, slotToInsert);
        //    // Insert the new node into the current slot.
        //    hashTable[hashcode] = new TokenHashValue(str, tokenType, tokenValue); ;

        //    while (++pos < TOKEN_HASH_SIZE)
        //    {
        //        hashcode += hashProbe;
        //        if (hashcode >= TOKEN_HASH_SIZE) hashcode -= TOKEN_HASH_SIZE;
        //        // Remember this slot
        //        TokenHashValue temp = hashTable[hashcode];

        //        if (temp != null && Char.ToLower(temp.tokenString[0], this.Culture) != ch)
        //        {
        //            continue;
        //        }
        //        // Put the previous slot into this slot.
        //        hashTable[hashcode] = previousNode;
        //        //// //////Console.WriteLine("  Move {0} to slot {1}", previousNode.tokenString, hashcode);
        //        if (temp == null)
        //        {
        //            // Done
        //            return;
        //        }
        //        previousNode = temp;
        //    };
        //    Contract.Assert(true, "The hashtable is full.  This should not happen.");
        //}

        //    void InsertHash(TokenHashValue[] hashTable, String str, TokenType tokenType, int tokenValue)
        //    {
        //        // The month of the 13th month is allowed to be null, so make sure that we ignore null value here.
        //        if (str == null || str.Length == 0)
        //        {
        //            return;
        //        }
        //        TokenHashValue value;
        //        int i = 0;
        //        // If there is whitespace characters in the beginning and end of the string, trim them since whitespaces are skipped by
        //        // StarDate.Parse().
        //        if (Char.IsWhiteSpace(str[0]) || Char.IsWhiteSpace(str[str.Length - 1]))
        //        {
        //            str = str.Trim(null);   // Trim white space characters.
        //            // Could have space for separators
        //            if (str.Length == 0)
        //                return;
        //        }
        //        char ch = Char.ToLower(str[0], this.Culture);
        //        int hashcode = ch % TOKEN_HASH_SIZE;
        //        int hashProbe = 1 + ch % SECOND_PRIME;
        //        do
        //        {
        //            value = hashTable[hashcode];
        //            if (value == null)
        //            {
        //                //// //////Console.WriteLine("   Put Key: {0} in {1}", str, hashcode);
        //                hashTable[hashcode] = new TokenHashValue(str, tokenType, tokenValue);
        //                return;
        //            }
        //            else
        //            {
        //                // Collision happens. Find another slot.
        //                if (str.Length >= value.tokenString.Length)
        //                {
        //                    // If there are two tokens with the same prefix, we have to make sure that the longer token should be at the front of
        //                    // the shorter ones.
        //                    if (String.Compare(str, 0, value.tokenString, 0, value.tokenString.Length, this.Culture, CompareOptions.IgnoreCase) == 0)
        //                    {
        //                        if (str.Length > value.tokenString.Length)
        //                        {
        //                            // The str to be inserted has the same prefix as the current token, and str is longer.
        //                            // Insert str into this node, and shift every node behind it.
        //                            InsertAtCurrentHashNode(hashTable, str, ch, tokenType, tokenValue, i, hashcode, hashProbe);
        //                            return;
        //                        }
        //                        else
        //                        {
        //                            // Same token.  If they have different types (regular token vs separator token).  Add them.
        //                            // If we have the same regular token or separator token in the hash already, do NOT update the hash.
        //                            // Therefore, the order of inserting token is significant here regarding what tokenType will be kept in the hash.


        //                            //
        //                            // Check the current value of RegularToken (stored in the lower 8-bit of tokenType) , and insert the tokenType into the hash ONLY when we don't have a RegularToken yet.
        //                            // Also check the current value of SeparatorToken (stored in the upper 8-bit of token), and insert the tokenType into the hash ONLY when we don't have the SeparatorToken yet.
        //                            //

        //                            int nTokenType = (int)tokenType;
        //                            int nCurrentTokenTypeInHash = (int)value.tokenType;

        //                            // The idea behind this check is:
        //                            // - if the app is targetting 4.5.1 or above OR the compat flag is set, use the correct behavior by default.
        //                            // - if the app is targetting 4.5 or below AND the compat switch is set, use the correct behavior
        //                            // - if the app is targetting 4.5 or below AND the compat switch is NOT set, use the incorrect behavior
        //                            if (preferExistingTokens || BinaryCompatibility.TargetsAtLeast_Desktop_V4_5_1)
        //                            {
        //                                if (((nCurrentTokenTypeInHash & (int)TokenType.RegularTokenMask) == 0) && ((nTokenType & (int)TokenType.RegularTokenMask) != 0) ||
        //                                   ((nCurrentTokenTypeInHash & (int)TokenType.SeparatorTokenMask) == 0) && ((nTokenType & (int)TokenType.SeparatorTokenMask) != 0))
        //                                {
        //                                    value.tokenType |= tokenType;
        //                                    if (tokenValue != 0)
        //                                    {
        //                                        value.tokenValue = tokenValue;
        //                                    }
        //                                }
        //                            }
        //                            else
        //                            {
        //                                // The following logic is incorrect and causes updates to happen depending on the bitwise relationship between the existing token type and the
        //                                // the stored token type.  It was this way in .NET 4 RTM.  The behavior above is correct and will be adopted going forward.

        //                                if ((((nTokenType | nCurrentTokenTypeInHash) & (int)TokenType.RegularTokenMask) == nTokenType) ||
        //                                   (((nTokenType | nCurrentTokenTypeInHash) & (int)TokenType.SeparatorTokenMask) == nTokenType))
        //                                {
        //                                    value.tokenType |= tokenType;
        //                                    if (tokenValue != 0)
        //                                    {
        //                                        value.tokenValue = tokenValue;
        //                                    }
        //                                }
        //                            }
        //                            // The token to be inserted is already in the table.  Skip it.
        //                        }
        //                    }
        //                }
        //            }
        //            //// //////Console.WriteLine("  COLLISION. Old Key: {0}, New Key: {1}", hashTable[hashcode].tokenString, str);
        //            i++;
        //            hashcode += hashProbe;
        //            if (hashcode >= TOKEN_HASH_SIZE) hashcode -= TOKEN_HASH_SIZE;
        //        } while (i < TOKEN_HASH_SIZE);
        //        Contract.Assert(true, "The hashtable is full.  This should not happen.");
        //    }
        //}   // class StarCulture

        internal class TokenHashValue
        {
            internal String tokenString;
            internal TokenType tokenType;
            internal int tokenValue;

            internal TokenHashValue(String tokenString, TokenType tokenType, int tokenValue)
            {
                this.tokenString = tokenString;
                this.tokenType = tokenType;
                this.tokenValue = tokenValue;
            }
        }

        public static StarCulture GetInstance(IFormatProvider provider)
        {
            //// Fast case for a regular CultureInfo
            //DateTimeFormatInfo info;
            //CultureInfo cultureProvider = provider as CultureInfo;
            //if (cultureProvider != null && !cultureProvider.m_isInherited)
            //{
            //    return cultureProvider.DateTimeFormat;
            //}
            //// Fast case for a DTFI;
            //info = provider as DateTimeFormatInfo;
            //if (info != null)
            //{
            //    return info;
            //}
            //// Wasn't cultureInfo or DTFI, do it the slower way
            //if (provider != null)
            //{
            //    info = provider.GetFormat(typeof(DateTimeFormatInfo)) as DateTimeFormatInfo;
            //    if (info != null)
            //    {
            //        return info;
            //    }
            //}
            // Couldn't get anything, just use currentInfo as fallback
            return CurrentCulture;
        }

        public int ID
        {
            get
            {
                return iD;
            }

            internal set
            {
                iD = value;
            }
        }


        public string MonthDayPattern { get => monthDayPattern1; private set => monthDayPattern1 = value; }
        public string[] saShortDates
        {
            get
            {
                if (saShortDates1 == null)
                {
                    saShortDates1 = InvariantCulture.saShortDates1;
                }
                return saShortDates1;
            }

            private set
            {
                saShortDates1 = value;
            }
        }

        public string[] saLongDates
        {
            get
            {
                if (saLongDates1 == null)
                {
                    saLongDates1 = InvariantCulture.saLongDates1;
                }
                return saLongDates1;
            }

            private set
            {
                saLongDates1 = value;
            }
        }
        public string[] saYearMonths
        {
            get
            {
                if (saYearMonths1 == null)
                {
                    saYearMonths1 = InvariantCulture.saYearMonths1;
                }
                return saYearMonths1;
            }

            private set
            {
                saYearMonths1 = value;
            }
        }
        public string sMonthDay
        {
            get
            {
                if (sMonthDay1 == null)
                {
                    sMonthDay1 = InvariantCulture.sMonthDay1;
                }
                return sMonthDay1;
            }

            private set
            {
                sMonthDay1 = value;
            }
        }

        public static StarCulture[] Cultures
        {
            get
            {
                if (cultures == null)
                {
                    cultures = new StarCulture[dict.Count];
                    int i = 0;
                    foreach (var entry in dict)
                    {
                        if (entry.Value.sISO639LANGNAME == "en")
                        {
                            StarCulture culture1 = entry.Value;
                            StarCulture culture2 = cultures[0];
                            cultures[0] = culture2;
                            cultures[i] = culture1;
                        }
                        else
                        {
                            cultures[i] = entry.Value;
                        }
                        i++;
                    }
                }
                return cultures;
            }
        }

        private static StarCulture[] cultures;

        //public static StarCulture InvariantCulture;

        public static int CAL_HEBREW = V;
        private int iD = 42;
        [NonSerialized]
        private string[] saShortDates1;
        [NonSerialized]
        private string[] saLongDates1;
        [NonSerialized]
        private string sMonthDay1;
        [NonSerialized]
        private string[] saYearMonths1;
        [NonSerialized]
        private string[] saMonthNames;
        private bool bUseUserOverrides;
        [NonSerialized]
        private string[] shortTimes;
        [NonSerialized]
        private string[] longTimes;
        [NonSerialized]
        private string sPM2359;
        [NonSerialized]
        private string sAM1159;
        internal bool ThirtyHour = false;
        [NonSerialized]
        private string sISO639LANGNAME;
        [NonSerialized]
        private string cultureName;
        [NonSerialized]
        private string monthDayPattern1;



        //private string[] m_genitiveAbbreviatedMonthNames;

        //private string[] saSuperShortDayNames1;
        //private string[] superShortDayNames;

        //private string[] saAbbrevDayNames1;


        //public StarCulture(StarCulture starDateFormatInfo)
        //{
        //    this.starDateFormatInfo = starDateFormatInfo;
        //}

        //public static BigInteger TicksPerSecond { get; internal set; }

        internal StarCulture GetDefaultInstance()
        {
            throw new NotImplementedException();
        }

        //internal StarCulture Clone()
        //{
        //    throw new NotImplementedException();
        //}

        internal void SetReadOnlyState(bool m_isReadOnly)
        {
            throw new NotImplementedException();
        }

        //internal StarCulture ReadOnly(StarCulture calendar)
        //{
        //    throw new NotImplementedException();
        //}

        internal int GetYear(object minSupportedStarDate)
        {
            throw new NotImplementedException();
        }

        //internal int GetYear(object maxSupportedStarDate)
        //{
        //    throw new NotImplementedException();
        //}

        internal bool IsLeapYear(int year)
        {
            throw new NotImplementedException();
        }

        internal object GetEra(StarDate starDate)
        {
            throw new NotImplementedException();
        }

        internal int GetDayOfMonth(StarDate starDate)
        {
            return starDate.Day;
        }

        internal DayOfWeek GetDayOfWeek(StarDate starDate)
        {
            return starDate.DayOfWeek;
        }

        internal int GetMonth(StarDate starDate)
        {
            return starDate.Month;
        }

        public object Clone()
        {
            throw new NotImplementedException();
        }

        object IFormatProvider.GetFormat(Type formatType)
        {
            return FormatProvider;
        }

        public override bool Equals(object obj)
        {
            return obj is StarCulture culture &&
                   generalLongTimePattern == culture.generalLongTimePattern;
        }

        public override int GetHashCode()
        {
            throw new NotImplementedException();
        }
    }
}