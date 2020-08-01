// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==


using System;
using System.Collections.Generic;
using System.IO;
using System.Globalization;
using System.Reflection;
using System.Diagnostics.Contracts;
//using System.Globalization;

namespace StarLib
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


    //[Serializable]
    [System.Runtime.InteropServices.ComVisible(true)]
    public sealed class StarCulture : IFormatProvider
    {
        private static Dictionary<string, StarCulture> isodict = getformats();
        private static StarCulture invariantCulture;
        private static StarCulture currentCulture = GetCurrentCulture();

        private static StarCulture GetCurrentCulture()
        {
            try
            {
                return isodict[CultureInfo.CurrentCulture.TwoLetterISOLanguageName];
            }
            catch (KeyNotFoundException)
            {
                isodict = importformats();
                try
                {
                    return isodict[CultureInfo.CurrentCulture.TwoLetterISOLanguageName];
                }
                catch (KeyNotFoundException)
                {
                    return InvariantCulture;
                }
            }
        }

        public static StarCulture CurrentCulture
        {
            get
            {
                return currentCulture;
            }
        }

        public static StarCulture InvariantCulture { get => invariantCulture; }

        public static void UpdateCulture()
        {
            currentCulture = GetCurrentCulture();
        }

        public static StarCulture GetStarCulture(string TwoLetterISOLanguageName)
        {
            return isodict[TwoLetterISOLanguageName];
        }



        internal bool m_isInherited = false;
        private IFormatProvider formatProvider;
        //[NonSerialized]
        private string[] monthGenitives;
        ////[NonSerialized]

        //internal static StarCulture Symbols;
        //[NonSerialized]
        private string langfam;
        //[NonSerialized]
        private string sNativeName;
        //[NonSerialized]
        private string notes;
        //[NonSerialized]
        private string[] dayNames = new string[7];
        //[NonSerialized]
        private List<string> months;
        //[NonSerialized]
        private List<string> saMonthGenitiveNames;
        //[NonSerialized]
        private List<string> misc;
        //[NonSerialized]
        private string dateSeparator = "-";

        private static Dictionary<string, StarCulture> getformats()
        {
            isodict = new Dictionary<string, StarCulture>();
            invariantCulture = new StarCulture("English", "en", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus",
                                                            "Gemini", "Karkino", "Leo", "Virgo", "Libra", "Scorpio", "Ophiuchus", "Horus");

            StarCulture JapaneseCulture = new StarCulture("Japanese", "ja", "日曜日", "月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "射手座", "山羊座", "水瓶座", "魚座", "牡羊座", "牡牛座", "双児宮", "巨蟹宮", "獅子宮", "乙女座", "天秤座", "蠍座", "へびつかい座", "ホルス");
            StarCulture ChineseCulture = new StarCulture("Chinese", "zh", "人馬座", "摩羯座", "水瓶座", "雙魚座", "白羊座", "金牛座", "雙子座", "巨蟹座", "獅子座", "處女座", "天秤座", "天蠍座", "蛇夫座", "荷魯斯");
            StarCulture Hindi = new StarCulture("Hindi", "hi", "धनु", "मकर", "कुम्भ", "मत्स्य", "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक", "सर्पधारी", "विष्णु");
            StarCulture Russian = new StarCulture("Russian", "ru", "Стрелец", "Козерог", "Водолей", "Рыбы", "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Змееносец", "Дажьбог");
            StarCulture French = new StarCulture("French", "fr", "Sagittaire", "Capricorne", "Verseau", "Poissons", "Bélier", "Taureau", "Gémeaux", "Karkino", "Lion", "Vierge", "Balance", "Scorpion", "Ophiuchus", "Horus");
            StarCulture Portugese = new StarCulture("Portugese", "pt", "Sagitário", "Capricórnio", "Aquário", "Peixes", "Áries", "Touro", "Gêmeos", "Karkino", "Leão", "Virgem", "Libra", "Escorpião", "Ophiuchus", "Hórus");
            StarCulture Spanish = new StarCulture("Spanish", "es", "Sagitario", "Capricornio", "Acuario", "Piscis", "Aries", "Tauro", "Géminis", "Karkino", "Leo", "Virgo", "Libra", "Escorpio", "Ofiuco", "Horus");
            StarCulture Arabic = new StarCulture("Arabic", "ar", "القوس", "الجدي", "الدلو", "الحوت", "الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء", "الميزان", "العقرب", "الحواء", "ذو_القرنين");
            // Formats
            InvariantCulture.saShortDates = new String[] { "MM/dd/yyyy", "yyyy-MM-dd" };          // short date format
            InvariantCulture.saLongDates = new String[] { "dddd, dd MMMM yyyy" };                 // long date format
            InvariantCulture.saYearMonths = new String[] { "yyyy MMMM" };                         // Year month format
            InvariantCulture.sMonthDay = "MMMM dd";                                            // Month day pattern

            // Calendar Parts Names
            //InvariantCulture.saEraNames = new String[] { "A.D." };     // Era names
            //InvariantCulture.saAbbrevEraNames = new String[] { "AD" };      // Abbreviated Era names
            //InvariantCulture.saAbbrevEnglishEraNames = new String[] { "AD" };     // Abbreviated era names in English
            InvariantCulture.dayNames = new String[] { "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" };// day names
            InvariantCulture.AbbreviatedDayNames = new String[] { "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" };     // abbreviated day names
            InvariantCulture.SuperShortDayNames = new String[] { "Su", "Mo", "Tu", "We", "Th", "Fr", "Sa" };      // The super short day names
            InvariantCulture.MonthNames = new String[] { "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus",
                                                            "Gemini", "Karkino", "Leo", "Virgo", "Libra", "Scorpio", "Ophiuchus", "Horus"}; // month names
            InvariantCulture.m_genitiveAbbreviatedMonthNames = new String[] { "Sag", "Cap", "Aqu", "Pis", "Ari", "Tau",
                                                            "Gem", "Kar", "Leo", "Vir", "Lib", "Sco", "Oph", "Hor"}; // abbreviated month names
                                                                                                                     // Time
            InvariantCulture.dateSeparator = "-";
            InvariantCulture.TimeSeparator = ":";
            InvariantCulture.SAM1159 = "AM";                   // AM designator
            InvariantCulture.SPM2359 = "PM";                   // PM designator
            InvariantCulture._longtimes = new string[] { "HH:mm:ss" };                             // time format
            InvariantCulture._saShortTimes = new string[] { "HH:mm", "hh:mm tt", "H:mm", "h:mm tt" }; // short time format
            InvariantCulture._saDurationFormats = new string[] { "HH:mm:ss" };                             // time duration format
            InvariantCulture.shortTimePattern = "h:mm tt";
            InvariantCulture.longTimePattern = "HH:mm:ss";
            InvariantCulture.LongDatePattern = "WWWW MMMMM ddd yyyyy";
            InvariantCulture.shortDatePattern = "yyyyy/MM/dd";
            InvariantCulture.m_genitiveAbbreviatedMonthNames = InvariantCulture.AbbreviatedGenitiveMonthNames;    // Abbreviated genitive month names (same as abbrev month names for invariant)                                                      
            JapaneseCulture.shortTimePattern = "h時m分s秒";
            ChineseCulture.shortTimePattern = "h時m分s秒";
            // Calendar was built, go ahead and assign it...            
            //Invariant = invariant;
            return isodict;
        }

        private static Dictionary<string, StarCulture> importformats()
        {
            throw new NotImplementedException();
        }


        private StarCulture(string line)
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
                            StarCulture.invariantCulture = this;
                        }
                        if (CultureName == "Japanese")
                        {
                            this.shortTimePattern = "h時m分s秒";
                        }
                        if (CultureName == "Chinese")
                        {
                            this.shortTimePattern = "h時m分s秒";
                        }
                        break;
                    case 1:
                        this.langfam = n[i];
                        break;
                    case 2:
                        this.sNativeName = n[i];
                        break;
                    case 3:
                        this.TwoLetterISO = n[i];
                        isodict.Add(this.TwoLetterISO, this);
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
                        this.dayNames[1] = n[i];
                        break;
                    case 9:
                        this.dayNames[2] = n[i];
                        break;
                    case 10:
                        this.dayNames[3] = n[i];
                        break;
                    case 11:
                        this.dayNames[4] = n[i];
                        break;
                    case 12:
                        this.dayNames[5] = n[i];
                        break;
                    case 13:
                        this.dayNames[6] = n[i];
                        break;
                    case 14:
                        this.dayNames[0] = n[i];
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
                        this.dateSeparator = n[i];
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
            this.importnet();

        }

        public StarCulture(string language, string iso, string v, string v2, string v3, string v4, string v5, string v6, string v7, string v8, string v9, string v10, string v11, string v12, string v13, string v14, string v15, string v16, string v17, string v18, string v19, string v20, string v21)
        {
            this.cultureName = language;
            this.sISO639LANGNAME = iso;
            this.dayNames = new string[] { v, v2, v3, v4, v5, v6, v7 };
            this.monthNames = new string[] { v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21 };
            this.importnet();
            isodict.Add(this.TwoLetterISO, this);
        }

        internal bool GetAbbreviatedEraName(StarDate starDate)
        {
            throw new NotImplementedException();
        }

        internal bool GetEraName(StarDate starDate)
        {
            throw new NotImplementedException();
        }

        public StarCulture(string v1, string v2, string v3, string v4, string v5, string v6, string v7, string v8, string v9, string v10, string v11, string v12, string v13, string v14, string v15, string v16)
        {
            this.cultureName = v1;
            this.sISO639LANGNAME = v2;
            this.monthNames = new string[] { v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16 };
            this.importnet();
            isodict.Add(this.TwoLetterISO, this);
        }

        private void importnet()
        {
            try
            {
                //CultureInfo culture = GetCultureInfo(this.TwoLetterISO);
                CultureInfo culture = CultureInfo.CurrentCulture;
                this.dayNames = culture.DateTimeFormat.DayNames;
                //this.timeSeparator = culture.DateTimeFormat.TimeSeparator;
                this.AMDesignator = culture.DateTimeFormat.AMDesignator;
                this.PMDesignator = culture.DateTimeFormat.PMDesignator;
                this.LongDatePattern = NetConvert(culture.DateTimeFormat.LongDatePattern);
                this.ShortDatePattern = NetConvert(culture.DateTimeFormat.ShortDatePattern);
                //this.dateSeparator = culture.DateTimeFormat.DateSeparator;
                this.longTimePattern = culture.DateTimeFormat.LongTimePattern;
                this.shortTimePattern = culture.DateTimeFormat.ShortTimePattern;
                this.FullStarDatePattern = NetConvert(culture.DateTimeFormat.FullDateTimePattern);
                this.AbbreviatedDayNames = culture.DateTimeFormat.AbbreviatedDayNames;
                this.SuperShortDayNames = culture.DateTimeFormat.ShortestDayNames;
                this.YearMonthPattern = culture.DateTimeFormat.YearMonthPattern;
            }
            catch (CultureNotFoundException)
            {

            }
        }



        private string NetConvert(string pat)
        {
            if (pat.Contains("dddd"))
            {
                int i = pat.IndexOf("dddd");
                char[] p = pat.ToCharArray();
                p[i] = 'W';
                p[i + 1] = 'W';
                p[i + 2] = 'W';
                p[i + 3] = 'W';
                pat = "";
                foreach (char c in p)
                {
                    pat += c;
                }
            }
            else if (pat.Contains("ddd"))
            {
                int i = pat.IndexOf("ddd");
                char[] p = pat.ToCharArray();
                p[i] = 'W';
                p[i + 1] = 'W';
                p[i + 2] = 'W';
                foreach (char c in p)
                {
                    pat += c;
                }
            }
            return pat;
        }

        internal string month(int m)
        {
            return this.months[m];
        }

        internal string WeekDays(int d)
        {
            return this.dayNames[d];
        }

        internal static StarCulture GetLocale(string lang)
        {
            try
            {
                return isodict[lang];
            }
            catch (KeyNotFoundException)
            {
                isodict = importformats();
                return isodict[lang];
            }
        }

        internal string StarDateString(StarDate dt, string format)
        {
            ////////////Console.WriteLine(this.CultureName);
            ////////////Console.WriteLine(this == null);
            return StarDateFormat.Format(dt, format, this);
        }






        internal string[] AbbreviatedDayNames
        {
            get
            {
                if (saAbbrevDayNames1 == null)
                {
                    string[] vs = new string[7];
                    int i = 1;
                    while (i < vs.Length)
                    {
                        vs[i] = abbreviate(WeekDays(i));
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

        internal string[] SuperShortDayNames
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



        internal string CultureName { get => cultureName; set => cultureName = value; }
        internal string TwoLetterISO { get => sISO639LANGNAME; set => sISO639LANGNAME = value; }

        //[NonSerialized]
        private List<string> ISO;

        internal string SAM1159
        {
            get
            {
                if (sAM1159 == null)
                {
                    sAM1159 = InvariantCulture.SAM1159;
                }
                return sAM1159;
            }

            set
            {
                sAM1159 = value;
            }
        }
        internal string SPM2359
        {
            get
            {
                if (sPM2359 == null)
                {
                    sPM2359 = InvariantCulture.SPM2359;
                }
                return sPM2359;
            }

            set
            {
                sPM2359 = value;
            }
        }
        internal string[] LongTimes
        {
            get
            {
                if (this._longtimes == null)
                {
                    this._longtimes = InvariantCulture._longtimes;
                }
                return _longtimes;
            }

            set
            {
                _longtimes = value;
            }
        }
        internal string[] ShortTimes { get => shortTimes; set => shortTimes = value; }
        internal bool UseUserOverride { get; set; }

        internal IFormatProvider FormatProvider
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

        internal string[] GenitiveMonthNames
        {
            get
            {
                string[] gen = new string[saMonthGenitiveNames.Count];
                int i = 0;
                while (i < saMonthGenitiveNames.Count)
                {
                    if (saMonthGenitiveNames[i] == "")
                    {
                        gen[i] = LatinGenitives[i];
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



        ////////////////////////////////////////////////////////////////////////////
        //
        // Create an array of string which contains the day names.
        //
        ////////////////////////////////////////////////////////////////////////////

        internal string[] GetDayNames()
        {
            string[] days = new string[7];
            int i = 0;
            while (i < days.Length)
            {
                days[i] = DayNames[i];
            }
            return days;
        }

        internal String[] DayNames
        {
            get
            {
                if (dayNames == null)
                {
                    dayNames = InvariantCulture.GetDayNames();
                }
                return dayNames;
            }

            set
            {
                dayNames = value;
            }
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
                            gen[i] = LatinGenitives[i];
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






        internal void WriteAllWeekDays()
        {
            var names = DayNames;
            int i = 0;
            while (i < names.Length)
            {
                //Console.WriteLine(i + " " + names[i]);
                i++;
            }
        }

        //

        internal IFormatProvider GetFormatProvider()
        {
            return this.FormatProvider;
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
        ////[NonSerialized] private StarCulture m_cultureData;

        // The culture name used to create this sdfi.
        ////[OptionalField(VersionAdded = 2)]
        //[NonSerialized]
        internal String m_name = null;

        // The language name of the culture used to create this sdfi.
        //[NonSerialized] private String m_langName = null;

        //
        // Caches for various properties.
        //

        // 

        //[NonSerialized]
        internal String amDesignator = null;
        //[NonSerialized]
        internal String pmDesignator = null;
        ////[OptionalField(VersionAdded = 1)]
        //[NonSerialized]
        //internal String dateSeparator = null;            // derived from short date (whidbey expects, arrowhead doesn't)
        //////[OptionalField(VersionAdded = 1)]
        ////[NonSerialized]
        internal String generalShortTimePattern = null;     // short date + short time (whidbey expects, arrowhead doesn't)
        ////[OptionalField(VersionAdded = 1)]
        //[NonSerialized]
        internal String generalLongTimePattern = null;     // short date + long time (whidbey expects, arrowhead doesn't)
        ////[OptionalField(VersionAdded = 1)]
        //[NonSerialized]
        //internal String timeSeparator = null;            // derived from long time (whidbey expects, arrowhead doesn't)
        internal String monthDayPattern = null;
        //////[OptionalField(VersionAdded = 2)]                  // added in .NET Framework Release {2.0SP1/3.0SP1/3.5RTM}
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

        ////[OptionalField(VersionAdded = 1)]
        //[NonSerialized]
        internal String fullStarDatePattern = null;        // long date + long time (whidbey expects, arrowhead doesn't)

        //[NonSerialized]
        internal String[] saAbbrevDayNames1 = null;

        ////[OptionalField(VersionAdded = 2)]
        //[NonSerialized]
        internal String[] superShortDayNames = null;
        //[NonSerialized]
        private String[] _abbreviatedMonthNames = null;
        //[NonSerialized]
        internal String[] monthNames = null;
        // Cache the genitive month names that we retrieve from the data table.
        ////[OptionalField(VersionAdded = 2)]
        //[NonSerialized]
        internal String[] genitiveMonthNames = null;

        // Cache the abbreviated genitive month names that we retrieve from the data table.
        ////[OptionalField(VersionAdded = 2)]
        //[NonSerialized]
        internal String[] m_genitiveAbbreviatedMonthNames = null;
        //[NonSerialized]
        private string[] _longtimes;
        //[NonSerialized]
        private string[] _saShortTimes;
        //[NonSerialized]
        private string[] _saDurationFormats;

        // Cache the month names of a leap Year that we retrieve from the data table.
        ////[OptionalField(VersionAdded = 2)]
        //[NonSerialized]
        internal String[] leapYearMonthNames = null;

        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]

        // The "default" Date/time patterns
        //[NonSerialized]
        internal String longDatePattern = null;
        //[NonSerialized]
        internal String shortDatePattern = null;
        //[NonSerialized]
        internal String yearMonthPattern = null;
        //[NonSerialized]
        internal String longTimePattern = null;
        //[NonSerialized]
        internal String shortTimePattern = null;

        public static readonly string[] MonthSymbols = new String[] { "♐︎", "♑︎", "♒︎", "♓︎", "♈︎", "♉︎",
                                                            "♊︎", "♋︎", "♌︎", "♍︎", "♎︎", "♏︎", "⛎", "🕎"}; // month names
        public static readonly string[] DaySymbols = new String[] { "☉", "☾", "火", "☿", "♃", "金", "♄" };// day names



        // These are Whidbey-serialization compatable arrays (eg: default not included)
        // "all" is a bit of a misnomer since the "default" pattern stored above isn't
        // necessarily a member of the list
        //[OptionalField(VersionAdded = 3)]
        //[NonSerialized]
        private String[] allYearMonthPatterns = null;   // This was wasn't serialized in Whidbey
        //[NonSerialized]
        internal String[] allShortDatePatterns = null;
        //[NonSerialized]
        internal String[] allLongDatePatterns = null;
        //[NonSerialized]
        internal String[] allShortTimePatterns = null;
        //[NonSerialized]
        internal String[] allLongTimePatterns = null;

        // Cache the era names for this StarCulture instance.
        //[NonSerialized]
        internal String[] m_eraNames = null;
        //[NonSerialized]
        internal String[] m_abbrevEraNames = null;
        //[NonSerialized]
        internal String[] m_abbrevEnglishEraNames = null;
        internal int[] optionalCalendars = null;

        private const int DEFAULT_ALL_StarDateS_SIZE = 132;

        internal string LongOrdinal(int day)
        {
            return Ordinal(day); //This is a long process that I don't feel the need to do now for getting all these words, 1st would be First 2nd would be Second and so on
        }

        // StarCulture updates this
        internal bool m_isReadOnly = false;

        // This flag gives hints about if formatting/parsing should perform special code csvFileName for things like
        // genitive form or leap Year month names.
        //[OptionalField(VersionAdded = 2)]
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



        // 
        //private String LanguageName
        //{
        //    [System.Security.SecurityCritical]  // auto-generated
        //    get
        //    {
        //        if (m_langName == null)
        //        {
        //            m_langName = this.TwoLetterISO;
        //        }
        //        return (m_langName);
        //    }
        //}

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



        internal String AMDesignator
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





        internal DayOfWeek FirstDayOfWeek
        {
            get
            {
                return DayOfWeek.Monday;
            }
        }






        internal String FullStarDatePattern
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
                fullStarDatePattern = value;
            }
        }


        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        internal String LongDatePattern
        {
            get
            {
                // Initialize our long date pattern from the 1st array value if not set
                if (this.longDatePattern == null)
                {
                    // Initialize our data
                    this.longDatePattern = InvariantCulture.longDatePattern;
                }

                return this.longDatePattern;
            }

            set
            {
                this.longDatePattern = value;
            }
        }

        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        internal String LongTimePattern
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
                //this.StarDateOffsetPattern = null;
            }
        }




        internal String PMDesignator
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


        internal String RFC1123Pattern
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
        internal String ShortDatePattern
        {
            get
            {
                // Initialize our short date pattern from the 1st array value if not set
                if (this.shortDatePattern == null)
                {
                    // Initialize our data
                    this.shortDatePattern = InvariantCulture.shortDatePattern;
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
                //StarDateOffsetPattern = null;
            }
        }


        // For our "patterns" arrays we have 2 variables, a string and a string[]
        //
        // The string[] contains the list of patterns, EXCEPT the default may not be included.
        // The string contains the default pattern.
        // When we initially construct our string[], we set the string to string[0]
        internal String ShortTimePattern
        {
            get
            {
                // Initialize our short time pattern from the 1st array value if not set
                if (this.shortTimePattern == null)
                {
                    // Initialize our data
                    this.shortTimePattern = InvariantCulture.shortTimePattern;
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


        internal String SortableStarDatePattern
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



        // Note that cultureData derives this from the long time format (unless someone's set this previously)
        // Note that this property is quite undesirable.
        // 
        internal string TimeSeparator
        {
            get
            {
                if (timeSeparator == null)
                {
                    timeSeparator = InvariantCulture.TimeSeparator;
                }
                return timeSeparator;
            }

            set
            {
                timeSeparator = value;
            }
        }

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

        //                timeSeparator = value;
        //            }
        //#endif
        //        }


        internal String UniversalSortableStarDatePattern
        {
            get
            {
                return (universalSortableStarDatePattern);
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

        // Returns the string array of the one-letter day of week names.
        //[System.Runtime.InteropServices.ComVisible(false)]
        internal String[] ShortestDayNames
        {
            get
            {
                return (String[])SuperShortDayNames.Clone();
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
                if (value.Length != 7)
                {
                    throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Argument_InvalidArrayLength", 7), "value");
                }
                Contract.EndContractBlock();
                CheckNullValue(value, value.Length);
                this.SuperShortDayNames = value;
            }
        }





        internal String[] AbbreviatedMonthNames
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
                _abbreviatedMonthNames = value;
            }
        }


        internal string[] MonthNames
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


        internal String GetAbbreviatedDayName(DayOfWeek dayofweek)
        {

            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
                                                     //"dayofweek", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
                                                     //  DayOfWeek.Sunday, DayOfWeek.Saturday));
            }
            Contract.EndContractBlock();
            //
            // Don't call the internal property AbbreviatedDayNames here since a clone is needed in that
            // property, so it will be slower.  Instead, use GetAbbreviatedDayOfWeekNames() directly.
            //
            return (internalGetAbbreviatedDayOfWeekNames()[(int)dayofweek]);
        }


        // Returns the super short day of week names for the specified day of week.
        [System.Runtime.InteropServices.ComVisible(false)]
        internal String GetShortestDayName(DayOfWeek dayOfWeek)
        {

            if ((int)dayOfWeek < 0 || (int)dayOfWeek > 6)
            {
                throw new NotImplementedException(); // throw new ArgumentOutOfRangeException(
                                                     //"dayOfWeek", //LEnvironment.GetResourceString("ArgumentOutOfRange_Range",
                                                     //DayOfWeek.Sunday, DayOfWeek.Saturday));
            }
            Contract.EndContractBlock();
            //
            // Don't call the internal property SuperShortDayNames here since a clone is needed in that
            // property, so it will be slower.  Instead, use internalGetSuperShortDayNames() directly.
            //
            return SuperShortDayNames[(int)dayOfWeek];
        }

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


        //internal String[] GetAllStarDatePatterns()
        //{
        //    List<String> results = new List<String>(DEFAULT_ALL_StarDateS_SIZE);

        //    for (int i = 0; i < StarDateFormat.allStandardFormats.Length; i++)
        //    {
        //        String[] strings = GetAllStarDatePatterns(StarDateFormat.allStandardFormats[i]);
        //        for (int j = 0; j < strings.Length; j++)
        //        {
        //            results.Add(strings[j]);
        //        }
        //    }
        //    return results.ToArray();
        //}


        //internal String[] GetAllStarDatePatterns(char format)
        //{
        //    Contract.Ensures(Contract.Result<String[]>() != null);
        //    String[] result = null;

        //    switch (format)
        //    {
        //        case 'd':
        //            result = this.AllShortDatePatterns;
        //            break;
        //        case 'D':
        //            result = this.AllLongDatePatterns;
        //            break;
        //        case 'f':
        //            result = GetCombinedPatterns(AllLongDatePatterns, AllShortTimePatterns, " ");
        //            break;
        //        case 'F':
        //        case 'U':
        //            result = GetCombinedPatterns(AllLongDatePatterns, AllLongTimePatterns, " ");
        //            break;
        //        case 'g':
        //            result = GetCombinedPatterns(AllShortDatePatterns, AllShortTimePatterns, " ");
        //            break;
        //        case 'G':
        //            result = GetCombinedPatterns(AllShortDatePatterns, AllLongTimePatterns, " ");
        //            break;
        //        case 'm':
        //        case 'M':
        //            //result = new String[] { MonthDayPattern };
        //            throw new NotImplementedException();
        //        case 'o':
        //        case 'O':
        //            result = new String[] { StarDateFormat.RoundtripFormat };
        //            break;
        //        case 'r':
        //        case 'R':
        //            result = new String[] { rfc1123Pattern };
        //            break;
        //        case 's':
        //            result = new String[] { sortableStarDatePattern };
        //            break;
        //        case 't':
        //            result = this.AllShortTimePatterns;
        //            break;
        //        case 'T':
        //            result = this.AllLongTimePatterns;
        //            break;
        //        case 'u':
        //            result = new String[] { UniversalSortableStarDatePattern };
        //            break;
        //        case 'y':
        //        case 'Y':
        //            result = this.AllYearMonthPatterns;
        //            break;
        //        default:
        //            throw new NotImplementedException(); // throw new ArgumentException(//LEnvironment.GetResourceString("Format_BadFormatSpecifier"), "format");
        //    }
        //    return (result);
        //}


        internal String GetDayName(DayOfWeek dayofweek)
        {
            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new ArgumentOutOfRangeException();
            }
            Contract.EndContractBlock();

            // Use the internal one so that we don't clone the array unnecessarily
            return DayNames[(int)dayofweek];
        }

        internal String GetShortDayName(DayOfWeek dayofweek)
        {
            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new ArgumentOutOfRangeException();
            }
            Contract.EndContractBlock();

            // Use the internal one so that we don't clone the array unnecessarily
            return (AbbreviatedDayNames[(int)dayofweek]);
        }

        internal String GetSuperShortDayName(DayOfWeek dayofweek)
        {
            if ((int)dayofweek < 0 || (int)dayofweek > 6)
            {
                throw new ArgumentOutOfRangeException();
            }
            Contract.EndContractBlock();

            // Use the internal one so that we don't clone the array unnecessarily
            return (SuperShortDayNames[(int)dayofweek]);
        }



        internal String GetAbbreviatedMonthName(int month)
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


        public String GetMonthNameFromIndex(int month)
        {
            return MonthNames[month];
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

        private string[] YearMonths()
        {
            throw new NotImplementedException();
        }

        // NOTE: Clone this string array if you want to return it to user.  Otherwise, you are returning a writable cache copy.
        // This won't include default, call AllLongDatePatterns


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




        internal bool IsReadOnly
        {
            get
            {
                return (m_isReadOnly);
            }
        }
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
        internal void SetAllStarDatePatterns(String[] patterns, char format)
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
        internal String[] AbbreviatedMonthGenitiveNames
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
        internal String[] MonthGenitiveNames
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
        //[NonSerialized]
        private string m_fullTimeSpanPositivePattern;
        internal String FullTimeSpanPositivePattern
        {
            get
            {
                if (m_fullTimeSpanPositivePattern == null)
                {
                    StarCulture cultureDataWithoutUserOverrides;
                    if (UseUserOverride)
                        cultureDataWithoutUserOverrides = this;
                    else
                        cultureDataWithoutUserOverrides = this;
                    String decimalSeparator = this.NumberDecimalSeparator;

                    m_fullTimeSpanPositivePattern = "d':'h':'mm':'ss'" + decimalSeparator + "'FFFFFFF";
                }
                return m_fullTimeSpanPositivePattern;
            }
        }

        //
        // Negative TimeSpan Pattern
        //
        //[NonSerialized]
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

        internal string GetDateSeparator()
        {
            if (dateSeparator == null)
            {
                dateSeparator = "-";
            }
            return dateSeparator;
        }

        internal void SetDateSeparator(string value)
        {
            dateSeparator = value;
        }
        //[NonSerialized]
        //private TokenHashValue[] m_sdfiTokenHash;
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

        }



        //private void AddMonthNames(TokenHashValue[] temp, String monthPostfix)
        //{
        //    for (int i = 1; i <= 13; i++)
        //    {
        //        String str;
        //        //str = internalGetMonthName(i, MonthNameStyles.Regular, false);
        //        // We have to call internal methods here to work with inherited sdfi.
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

        //    //// ////////////Console.WriteLine("   Insert Key: {0} in {1}", str, slotToInsert);
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
        //        //// ////////////Console.WriteLine("  Move {0} to slot {1}", previousNode.tokenString, hashcode);
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
        //                //// ////////////Console.WriteLine("   Put Key: {0} in {1}", str, hashcode);
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
        //            //// ////////////Console.WriteLine("  COLLISION. Old Key: {0}, New Key: {1}", hashTable[hashcode].tokenString, str);
        //            i++;
        //            hashcode += hashProbe;
        //            if (hashcode >= TOKEN_HASH_SIZE) hashcode -= TOKEN_HASH_SIZE;
        //        } while (i < TOKEN_HASH_SIZE);
        //        Contract.Assert(true, "The hashtable is full.  This should not happen.");
        //    }
        //}   // class StarCulture



        internal static StarCulture GetInstance(IFormatProvider provider)
        {
            //// Fast case for a regular CultureInfo
            if (CurrentCulture.formatProvider == provider)
            {
                return CurrentCulture;
            }
            else
            {
                foreach (StarCulture culture in cultures)
                {
                    if (culture.formatProvider == provider)
                    {
                        return culture;
                    }
                }
            }
            //Couldn't get anything, just use currentInfo as fallback
            return CurrentCulture;
        }

        internal int ID
        {
            get
            {
                return iD;
            }

            set
            {
                iD = value;
            }
        }


        private string[] saShortDates
        {
            get
            {
                if (saShortDates1 == null)
                {
                    saShortDates1 = InvariantCulture.saShortDates1;
                }
                return saShortDates1;
            }

            set
            {
                saShortDates1 = value;
            }
        }

        private string[] saLongDates
        {
            get
            {
                if (saLongDates1 == null)
                {
                    saLongDates1 = InvariantCulture.saLongDates1;
                }
                return saLongDates1;
            }

            set
            {
                saLongDates1 = value;
            }
        }
        private string[] saYearMonths
        {
            get
            {
                if (saYearMonths1 == null)
                {
                    saYearMonths1 = InvariantCulture.saYearMonths1;
                }
                return saYearMonths1;
            }

            set
            {
                saYearMonths1 = value;
            }
        }
        private string sMonthDay
        {
            get
            {
                if (sMonthDay1 == null)
                {
                    sMonthDay1 = InvariantCulture.sMonthDay1;
                }
                return sMonthDay1;
            }

            set
            {
                sMonthDay1 = value;
            }
        }

        internal static StarCulture[] Cultures
        {
            get
            {
                if (cultures == null)
                {
                    isodict = importformats();
                    cultures = new StarCulture[isodict.Count];
                    int i = 0;
                    foreach (var entry in isodict)
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

        internal string[] DaysOfTheWeek
        {
            get
            {
                if (this.dayNames == null)
                {
                    this.dayNames = InvariantCulture.DaysOfTheWeek;
                }
                return this.dayNames;
            }

            set
            {
                this.dayNames = value;
            }
        }





        internal string LongFormat { get => longFormat; set => longFormat = value; }
        internal string ShortFormat { get => shortFormat; set => shortFormat = value; }
        //public CultureInfo NetCulture
        //{
        //    get
        //    {
        //        return CultureInfo.GetCultureInfo(TwoLetterISO);
        //    }
        //}

        public string YearMonthPattern
        {
            get
            {
                if (yearMonthPattern == null)
                {
                    yearMonthPattern = InvariantCulture.yearMonthPattern;
                }
                return yearMonthPattern;
            }

            internal set
            {
                yearMonthPattern = value;
            }
        }


        private static StarCulture[] cultures;
        private int iD = 42;
        //[NonSerialized]
        private string[] saShortDates1;
        //[NonSerialized]
        private string[] saLongDates1;
        //[NonSerialized]
        private string sMonthDay1;
        //[NonSerialized]
        private string[] saYearMonths1;
        //[NonSerialized]
        private string[] saMonthNames;
        //[NonSerialized]
        private string[] shortTimes;
        //[NonSerialized]
        private string sPM2359;
        //[NonSerialized]
        private string sAM1159;
        internal bool ThirtyHour = false;
        //[NonSerialized]
        private string sISO639LANGNAME;
        //[NonSerialized]
        private string cultureName;
        //[NonSerialized]
        private string timeSeparator = ":";
        //[NonSerialized]
        private string shortFormat;
        //[NonSerialized]
        private string longFormat;
        //[NonSerialized]
        private string NumberDecimalSeparator = ".";
        private string[] LatinGenitives = new string[] { "Sagittarii", "Capricorni", "Aquarii", "Piscium", "Arietis", "Tauri", "Geminorum", "Karkinii", "Leonis", "Virginis", "Librae", "Scorpii", "Ophiuchi", "Horii" };

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

        object IFormatProvider.GetFormat(Type formatType)
        {
            return FormatProvider;
        }



        internal string Ordinal(int day)
        {
            switch (this.TwoLetterISO)
            {
                case "en":
                    switch (day)
                    {
                        case 11: return "11th";
                        case 12: return "12th";
                        case 13: return "13th";
                        default:
                            break;
                    }
                    String d = day.ToString(InvariantCulture.FormatProvider);
                    switch (d[d.Length - 1])
                    {
                        case '1':
                            return d + "st";
                        case '2':
                            return d + "nd";
                        case '3':
                            return d + "rd";
                        default:
                            return d + "th";
                    }
                case "fr":
                    if (day == 1)
                    {
                        return "1er";
                    }
                    else
                    {
                        return day + "e";
                    }
                default:
                    return "" + day;
            }
        }

        public string[] GetMonthList()
        {
            string[] vs = new string[14];
            int i = 0;
            while (i < 14)
            {
                vs[i] = MonthSymbols[i] + " " + MonthNames[i];
                i++;
            }
            return vs;
        }

        public string GetMonthList(int v)
        {
            return GetMonthList()[v - 1];
        }

        public string GetMonthName(int i)
        {
            throw new NotImplementedException();
        }
    }
}