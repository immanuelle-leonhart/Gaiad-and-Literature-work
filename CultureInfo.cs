using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;

namespace StarCalendar
{
    public class CultureInfo //combined cultureinfo and culturedata
    {
        //private string lang;
        private Dictionary<string, string> weekdays;
        private string[] months;
        //private Dictionary<int, string> numbers;
        private static Dictionary<string, CultureInfo> dict = getformats();
        private static string[] days = new string[] { "0", "mon", "tue", "wed", "thu", "fri", "sat", "sun" };

        public CultureInfo(string line)
        {
            string[] n = line.Split(',');
            this.CultureName = n[0];
            this.weekdays = new Dictionary<string, string>
        {
            {"0", "0"},
            {"mon", n[1]},
            {"tue", n[2]},
            {"wed", n[3]},
            {"thu", n[4]},
            {"fri", n[5]},
            {"sat", n[6]},
            {"sun", n[7]}
        };
            this.months = new string[] { "0", n[8], n[9], n[10], n[11], n[12], n[13], n[14], n[15], n[16], n[17], n[18], n[19], n[20], n[21] };
            //CultureInfo.dict.Add(this.lang, this);
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
            return this.weekdays[days[d]];
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
            string[] vs = new string[8];
            int i = 0;
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
            string[] vs = new string[8];
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
        public CultureInfo m_cultureData { get; internal set; }
        public int IFIRSTDAYOFWEEK { get; internal set; }
        public int IFIRSTWEEKOFYEAR { get; internal set; }
        public string SAM1159 { get; internal set; }
        public string SPM2359 { get; internal set; }
        public string TimeSeparator { get; internal set; }
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

        public static CultureInfo InvariantCulture = dict["English"];
        internal bool m_isInherited = false;
        private bool v;
        internal static CultureInfo CurrentCulture = dict["English"];
        private StarDateFormatInfo starDateInfo = new StarDateFormatInfo();

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

        internal string[] DayNames(object iD)
        {
            return DayNames();
        }

        private string[] DayNames()
        {
            throw new NotImplementedException();
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
            throw new NotImplementedException();
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
            throw new NotImplementedException();
        }

        internal string[] AbbreviatedGenitiveMonthNames(int iD)
        {
            throw new NotImplementedException();
        }

        internal string[] GenitiveMonthNames(int iD)
        {
            throw new NotImplementedException();
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

        //internal string month(int month)
        //{
        //    //return this.month
        //}
    }
}