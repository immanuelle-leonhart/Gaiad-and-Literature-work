using Microsoft.AspNetCore.Components;
using StarLib;
using System.Collections.Generic;

namespace StarBlaze.StarCalendar
{
    public class CalendarBase : ComponentBase
    {
        
        protected StarDate dt = StarDate.Now;
        private static List<int> month28;
        private static List<int> month14;
        private static List<int> month7;
        private static Dictionary<int, string> leapList;
        private static Dictionary<int, string> commonList;
        public static string test = "Test";

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
                if (dt.isleapyear())
                {
                    return LeapList;
                }
                else
                {
                    return CommonList;
                }
            }
        }

        public List<int> DayList
        {
            get
            {
                if (Month != 14)
                {
                    if (month28 == null)
                    {
                        month28 = new List<int>();
                        int i = 1;
                        while (i < 29)
                        {
                            month28.Add(i++);
                        }
                    }
                    return month28;
                }
                else if (dt.isDoubleLeapYear())
                {
                    if (month14 == null)
                    {
                        month14 = new List<int>();
                        int i = 1;
                        while (i < 15)
                        {
                            month14.Add(i++);
                        }
                    }
                    return month14;
                }
                else
                {
                    if (month7 == null)
                    {
                        month7 = new List<int>();
                        int i = 1;
                        while (i < 8)
                        {
                            month7.Add(i++);
                        }
                    }
                    return month7;
                }
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

        public Dictionary<int, string> CommonList
        {
            get
            {
                if (commonList == null)
                {
                    GenerateLists();
                }
                return commonList;
            }
        }

        public Dictionary<int, string> LeapList
        {
            get
            {
                if (leapList == null)
                {
                    GenerateLists();
                }
                return leapList;
            }
        }

        private void GenerateLists()
        {
            leapList = new Dictionary<int, string>();
            commonList = new Dictionary<int, string>();
            int i = 0;
            int j = 13;
            while (i < j)
            {
                string s = StarCulture.MonthSymbols[i] + " " + StarCulture.CurrentCulture.GetMonthNameFromIndex(i);
                commonList.Add(i + 1, s);
                leapList.Add(i + 1, s);
                i++;
            }
            leapList.Add(14, StarCulture.MonthSymbols[13] + " " + StarCulture.CurrentCulture.GetMonthNameFromIndex(13));
        }

        public override string ToString()
        {
            return dt;
        }

    }
}
