using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using StarLib;

namespace StarBlaze.Calendar
{
    public class CalendarBase
    {
        protected StarDate dt = StarDate.Now;

        public int Year { get => dt.Year; set => dt.Year = value; }
        public int Month { get => dt.Month; set => dt.Month = value; }
        public int Day { get => dt.Day; set => dt.Day = value; }
        public int Hour { get => dt.Hour; set => dt.Hour = value; }
        public int Minute { get => dt.Minute; set => dt.Minute = value; }
        public int Second { get => dt.Second; set => dt.Second = value; }
        public string Short { get => dt.ToShortString(); }
        public string Long { get => dt.ToLongString(); }

        public Dictionary<int, string> MonthList
        {
            get
            {
                Dictionary<int, string> months = new Dictionary<int, string>();
                int i = 0;
                int j = 13;
                if (dt.isleapyear())
                {
                    j = 14;
                }
                while (i < j)
                {
                    months.Add(i + 1, StarCulture.MonthSymbols[i] + " " + StarCulture.CurrentCulture.GetMonthNameFromIndex(i));
                    i++;
                }
                return months;
            }
        }

        public int Horus
        {
            get
            {
                if (dt.isDoubleLeapYear())
                {
                    return 14;
                }
                else if (dt.isleapyear())
                {
                    return 7;
                }
                else
                {
                    return 0;
                }
            }
        }

        public override string ToString()
        {
            return dt;
        }

    }
}
