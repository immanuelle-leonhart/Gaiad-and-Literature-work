using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;

namespace StarCalendar
{
    public class CultureInfo //combined cultureinfo and culturedata
    {
        //private string lang;
        //private Dictionary<string, string> weekdays;
        //private string[] months;
        //private string[] genmonths;

        //private Dictionary<int, string> numbers;
        private static Dictionary<string, CultureInfo> dict = getformats();
        //private static string[] days = new string[] { "0", "mon", "tue", "wed", "thu", "fri", "sat", "sun" };

        public CultureInfo(string line)
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
                            CultureInfo.InvariantCulture = this;
                        }
                        if (CultureName == "Symbol")
                        {
                            CultureInfo.Symbol = this;
                        }
                        break;
                    case 1:
                        this.langfam = n[i];
                        break;
                    case 2:
                        this.endonym = n[i];
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
                        this.weekdays = new List<string>() { n[i] };
                        break;
                    case 9:
                    case 10:
                    case 11:
                    case 12:
                    case 13:
                    case 14:
                        this.weekdays.Add(n[i]);
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
                        this.genmonths = new List<string> { n[i] };
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
                        this.genmonths.Add(n[i]);
                        break;
                    case 43:
                        this.SAM1159 = n[i];
                        break;
                    case 44:
                        this.SPM2359 = n[i];
                        break;
                    case 45:
                        this.hour_minute = n[i];
                        break;
                    case 46:
                        this.hour_second = n[i];
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
        //    this.weekdays = new Dictionary<string, string>
        //{
        //    {"0", "0"},
        //    {"mon", n[1]},
        //    {"tue", n[2]},
        //    {"wed", n[3]},
        //    {"thu", n[4]},
        //    {"fri", n[5]},
        //    {"sat", n[6]},
        //    {"sun", n[7]}
        //};
            //this.months = new string[] { "0", n[8], n[9], n[10], n[11], n[12], n[13], n[14], n[15], n[16], n[17], n[18], n[19], n[20], n[21] };
            //this.genmonths = new string[] { "0", n[22], n[23], n[24], n[25], n[26], n[27], n[28], n[29], n[30], n[31], n[32], n[33], n[34], n[35] };
            //this.starDateInfo = new StarDateFormatInfo(this);
            //this.SISO639LANGNAME = n[37];
            //this.SAM1159 = n[41];
            //if (SAM1159 == "")
            //{
            //    SAM1159 = "AM";
            //}
            //this.SPM2359 = n[42];
            //if (SPM2359 == "")
            //{
            //    SPM2359 = "PM";
            //}
            //this.hour_minute = n[43];
            //if (hour_minute == "")
            //{
            //    hour_minute = ":";
            //}
            //this.hour_second = n[44];
            //if (hour_second == "")
            //{
            //    hour_second = ":";
            //}

        }

        public CultureInfo(string line, bool v) : this(line)
        {
            this.v = v;
        }

        internal string month(int m)
        {
            return this.months[m];
        }

        internal string weekday(int d)
        {
            return this.weekdays[d - 1];
        }



        internal static CultureInfo GetLocale(string lang)
        {
            return dict[lang];
        }

        internal string StarDateString(StarDate dt, string format)
        {
            //Console.WriteLine(format);
            return StarDateFormat.Format(dt, format, StarDateFormatInfo.CurrentInfo);
        }

        //internal static CultureInfo InvariantCulture;
        //internal StarDateFormat DateTimeFormat;
        //private StarDateFormat starDateFormat;
        //private static CultureInfo currentCulture/* = dict["English"];*/
        //private StarDateFormat starDateFormat;
        //private static object invariantCulture;

        //public static CultureInfo CurrentCulture
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


                return new StarDateFormat(AbbreviatedMonthNames(), AbbreviatedDayNames());
            }

            //internal set
            //{
            //    starDateFormat = value;
            //}
        }

        private string[] AbbreviatedDayNames()
        {
            string[] vs = new string[7];
            int i = 1;
            while (i < vs.Length)
            {
                vs[i] = abbreviate(weekday(i));
                i++;
            }
            return vs;
        }

        private string abbreviate(string v)
        {
            string a = "" + v[0];
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
            return a;
        }

        private string[] AbbreviatedMonthNames()
        {
            string[] vs = new string[this.months.Count];
            int i = 0;
            while (i < vs.Length)
            {
                vs[i] = abbreviate(months[i]);
                i++;
            }
            return vs;
        }

        public string CultureName { get; internal set; }
        public string SISO639LANGNAME { get; internal set; }

        private List<string> ISO;

        //private Dictionary<int, string> ISO;

        public CultureInfo m_cultureData { get; internal set; }
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
        public string SAM1159 { get; internal set; }
        public string SPM2359 { get; internal set; }

        private string hour_minute;

        public string TimeSeparator { get { return hour_minute; } internal set => timeSeparator = value; }
        public string[] LongTimes { get; internal set; }
        public string[] ShortTimes { get; internal set; }
        public bool UseUserOverride { get; internal set; }
        public StarDateFormatInfo StarDateInfo
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
        public object SCOMPAREINFO { get; internal set; }
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

        public string[] MonthGenitives
        {
            get
            {
                string[] gen = new string[15];
                int i = 0;
                while (i < 15)
                {
                    if (genmonths[i] == "")
                    {
                        gen[i] = dict["Symbol"].genmonths[i];
                    }
                    else
                    {
                        gen[i] = genmonths[i];
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

        public static CultureInfo InvariantCulture = dict["English"];
        internal bool m_isInherited = false;
        private bool v;
        internal static CultureInfo CurrentCulture = dict["English"];
        private StarDateFormatInfo starDateInfo;
        private IFormatProvider formatProvider;
        private string[] monthGenitives;
        private int iFIRSTWEEKOFYEAR;
        private string hour_second;
        private string timeSeparator;
        private static CultureInfo Symbol;
        private string langfam;
        private string endonym;
        private string notes;
        private List<string> weekdays;
        private List<string> months;
        private List<string> genmonths;
        private List<string> misc;

        internal IFormatProvider GetFormat(Type type)
        {
            throw new NotImplementedException();
        }

        internal static CultureInfo GetCultureInfo(string cultureName)
        {
            throw new NotImplementedException();
        }

        internal string[] AbbreviatedDayNames(object iD)
        {
            return AbbreviatedDayNames();
        }

        internal string[] SuperShortDayNames(object iD)
        {
            return SuperShortDayNames();
        }

        private string[] SuperShortDayNames()
        {
            throw new NotImplementedException();
        }

        internal string[] DayNames(int iD)
        {
            return DayNames();
        }

        private string[] DayNames()
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

        internal string[] AbbreviatedMonthNames(object iD)
        {
            return AbbreviatedMonthNames();
        }

        internal string[] MonthNames(object iD)
        {
            return MonthNames();
        }

        private string[] MonthNames()
        {
            string[] vs = new string[this.months.Count];
            int i = 0;
            while (i < vs.Length)
            {
                vs[i] = months[i];
                i++;
            }
            return vs;
        }

        internal string DateSeparator(int calendarID)
        {
            throw new NotImplementedException();
        }

        internal string[] LongDates(int calendarID)
        {
            throw new NotImplementedException();
        }

        internal string[] ShortDates(int calendarID)
        {
            throw new NotImplementedException();
        }

        internal string[] YearMonths(int calendarID)
        {
            throw new NotImplementedException();
        }

        internal static CultureInfo GetCultureData(string m_name, bool m_useUserOverride)
        {
            throw new NotImplementedException();
        }

        internal static void CheckDomainSafetyObject(Calendar calendar, StarDateFormatInfo starDateFormatInfo)
        {
            throw new NotImplementedException();
        }

        internal IFormatProvider GetFormat()
        {
            return this.FormatProvider;
        }

        internal string[] AbbreviatedGenitiveMonthNames(int iD)
        {
            return AbbreviatedGenitiveMonthNames();
        }

        private string[] AbbreviatedGenitiveMonthNames()
        {
            string[] gen = new string[15];
            int i = 0;
            while (i < 15)
            {
                if (genmonths[i] == "")
                {
                    gen[i] = abbreviate(dict["Symbol"].genmonths[i]);
                }
                else
                {
                    gen[i] = abbreviate(genmonths[i]);
                }
                i++;
            }
            return gen;
        }

        internal string[] GenitiveMonthNames(int iD)
        {
            return this.MonthGenitives;
        }

        internal string[] AbbreviatedEnglishEraNames(int iD)
        {
            throw new NotImplementedException();
        }

        internal string MonthDay(int iD)
        {
            throw new NotImplementedException();
        }

        internal string[] LeapYearMonthNames(int iD)
        {
            throw new NotImplementedException();
        }

        internal string CalendarName(int iD)
        {
            throw new NotImplementedException();
        }

        private static Dictionary<string, CultureInfo> getformats()
        {
            int counter = 0;
            string line;
            Dictionary<string, CultureInfo> formats = new Dictionary<string, CultureInfo>();
            string path = "Languages.csv";
            //int lastslash = Gedcom.LastIndexOf('/');
            //string Filename = Gedcom.Substring(lastslash + 1);
            //Gedson ged = new Gedson();
            System.IO.StreamReader file = new StreamReader(path);
            while ((line = file.ReadLine()) != null)
            {
                //Console.WriteLine(line);
                CultureInfo form = new CultureInfo(line);
                formats.Add(form.CultureName, form);
                counter++;
            }
            return formats;
        }

        //

        public IFormatProvider GetFormatProvider()
        {
            return this.FormatProvider;
        }

        internal string[] GetDayNames()
        {
            return this.DayNames();
        }
    }
}