using System;
using System.Collections.Generic;

namespace StarCalendar
{
    class Program
    {
        //private static object Integers;

        static void Main(string[] args)
        {
            List<int> Integers = new List<int>();
            StarDate dt = StarDate.Now;
            StarDate utc = StarDate.UtcNow;
            Integers.Add(dt.fullyear);
            Integers.Add(dt.billion);
            Integers.Add(dt.million);
            Integers.Add(dt.year);
            Integers.Add(dt.DayOfYear);
            Integers.Add(dt.month);
            Integers.Add(dt.day);
            Integers.Add(dt.Hour);
            Integers.Add(dt.Minute);
            Integers.Add(dt.Second);
            Integers.Add(dt.Milliseconds);
            Integers.Add(dt.Ticks);
            string month = dt.MonthName;
            string WeekDay = dt.WeekDay;
            string Feast = dt.Feast;
        }
    }
}
