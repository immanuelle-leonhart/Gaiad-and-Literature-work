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
            Console.WriteLine(DateTime.Now.TimeOfDay);
            TimeSpanInfo t = dt.TimeOfDay;
            Integers.Add(t.Days);
            Integers.Add(t.Hours);
            Integers.Add(t.Minutes);
            Integers.Add(t.Seconds);
            Integers.Add(t.Milliseconds);
            //Integers.Add(t.ticks);
            // Get current DateTime. It can be any DateTime object in your code.  
            StarDate aDate = StarDate.Now;

            // Format Datetime in different formats and display them  
            Console.WriteLine(aDate.ToString("MM/dd/yyyy"));
            Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy HH:mm:ss"));
            Console.WriteLine(aDate.ToString("MM/dd/yyyy HH:mm"));
            Console.WriteLine(aDate.ToString("MM/dd/yyyy hh:mm tt"));
            Console.WriteLine(aDate.ToString("MM/dd/yyyy H:mm"));
            Console.WriteLine(aDate.ToString("MM/dd/yyyy h:mm tt"));
            Console.WriteLine(aDate.ToString("MM/dd/yyyy HH:mm:ss"));
            Console.WriteLine(aDate.ToString("MMMM dd"));
            Console.WriteLine(aDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss.fffffffK"));
            Console.WriteLine(aDate.ToString("ddd, dd MMM yyy HH’:’mm’:’ss ‘GMT’"));
            Console.WriteLine(aDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss"));
            Console.WriteLine(aDate.ToString("HH:mm"));
            Console.WriteLine(aDate.ToString("hh:mm tt"));
            Console.WriteLine(aDate.ToString("H:mm"));
            Console.WriteLine(aDate.ToString("h:mm tt"));
            Console.WriteLine(aDate.ToString("HH:mm:ss"));
            Console.WriteLine(aDate.ToString("yyyy MMMM"));
            Dictionary<string, TimeSpanInfo> times = new Dictionary<string, TimeSpanInfo>();
            //StarDate dt = StarDate.UtcNow;
            times.Add("atomic", dt.atomic);
            times.Add("radio", dt.Radio);
            times.Add("terra", dt.Terra);
            times.Add("arrival", dt.Arrival);
        }
    }
}
