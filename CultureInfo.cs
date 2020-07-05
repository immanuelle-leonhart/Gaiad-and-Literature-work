using System;
using System.Collections.Generic;

namespace StarCalendar
{
    public class CultureInfo
    {
        private string lang;
        private Dictionary<string, string> weekdays;
        private string[] months;
        //private Dictionary<int, string> numbers;
        private static Dictionary<string, CultureInfo> dict = new Dictionary<string, CultureInfo>();
        private static string[] days = new string[] { "0", "mon", "tue", "wed", "thu", "fri", "sat", "sun" };

        public CultureInfo(string line)
        {
            string[] n = line.Split(',');
            this.lang = n[0];
            this.weekdays = new Dictionary<string, string>
        {
            {"mon", n[1]},
            {"tue", n[2]},
            {"wed", n[3]},
            {"thu", n[4]},
            {"fri", n[5]},
            {"sat", n[6]},
            {"sun", n[7]}
        };
            this.months = new string[] { n[8], n[9], n[10], n[11], n[12], n[13], n[14], n[15], n[16], n[17], n[18], n[19], n[20], n[21] };
            CultureInfo.dict.Add(this.lang, this);
        }

        internal string month(int m)
        {
            return this.months[m + 1];
        }

        internal string weekday(int d)
        {
            return this.weekdays[days[d]];
        }



        internal static CultureInfo GetLocale(string lang)
        {
            return dict[lang];
        }

        internal string StarDateString(Dictionary<string, int> dictionary, string format)
        {
            throw new NotImplementedException();
        }

        internal static CultureInfo InvariantCulture;
        internal StarDateTimeFormatInfo DateTimeFormat;
        private StarDateTimeFormatInfo starDateFormat;
        private static IFormatProvider currentCulture;

        public static IFormatProvider CurrentCulture
        {
            get
            {
                return currentCulture;
            }

            internal set
            {
                currentCulture = value;
            }
        }
        public StarDateTimeFormatInfo StarDateFormat
        {
            get
            {
                return starDateFormat;
            }

            internal set
            {
                starDateFormat = value;
            }
        }

        internal IFormatProvider GetFormat()
        {
            throw new NotImplementedException();
        }
    }
}