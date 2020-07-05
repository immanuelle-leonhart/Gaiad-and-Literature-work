using System;
using System.Collections.Generic;

namespace StarCalendar
{
    class Program
    {
        //private static object Integers;

        static void Main(string[] args)
        {
            long b = 14000000000;
            List<int> Integers = new List<int>();
            StarDate dt = StarDate.Now;
            StarDate utc = StarDate.UtcNow;
            //Integers.Add(dt.fullyear);
            Integers.Add(dt.billion);
            Integers.Add(dt.million);
            Integers.Add(dt.year);
            Integers.Add(dt.DayOfYear);
            Integers.Add(dt.Month);
            Integers.Add(dt.day);
            Integers.Add(dt.Hour);
            Integers.Add(dt.Minute);
            Integers.Add(dt.Second);
            Integers.Add(dt.Milliseconds);
            //Integers.Add(dt.Ticks);
            string month = dt.MonthName;
            string WeekDay = dt.WeekDay;
            string Feast = dt.Feast;
            Console.WriteLine(DateTime.Now.TimeOfDay);
            TimeSpanInfo t = dt.TimeOfDay;
            Integers.Add(t.Days);
            Integers.Add(t.Hours);
            Integers.Add(t.Minutes);
            Integers.Add(t.Seconds);
            Integers.Add(t.Milliseconds);
            //Integers.Add(t.ticks);
        }
    }
}
