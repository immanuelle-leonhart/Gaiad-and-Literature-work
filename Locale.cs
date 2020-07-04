using System;
using System.Collections.Generic;

namespace StarCalendar
{
    public class Locale
    {
        private string lang;
        private Dictionary<string, string> weekdays;
        private string[] months;
        private Dictionary<int, string> numbers;
        private static Dictionary<string, Locale> dict = new Dictionary<string, Locale>();
        private static string[] days = new string[] { "0", "mon", "tue", "wed", "thu", "fri", "sat", "sun" };

        public Locale(string line)
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
            Locale.dict.Add(this.lang, this);
        }

        internal string month(int m)
        {
            return this.months[m + 1];
        }

        internal string weekday(int d)
        {
            return this.weekdays[days[d]];
        }

        

        internal static Locale GetLocale(string lang)
        {
            return dict[lang];
        }

        internal string StarDateString(Dictionary<string, int> dictionary, string format)
        {
            throw new NotImplementedException();
        }
    }
}