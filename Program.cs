using SpaceCalendar;
using System;
using System.Collections.Generic;
using System.Security.Cryptography.X509Certificates;

namespace StarCalendar
{
    class Program
    {
        //private static object Integers;

        static void Main(string[] args)
        {
            //long bi = 14000000000;
            //Console.WriteLine(bi);
            StarDate d = StarDate.Now;
            Console.WriteLine((c.maya + c.week).MonthName);
            List<int> Integers = new List<int>();
            StarDate dt = StarDate.Now;
            StarDate utc = StarDate.UtcNow;
            //Integers.Add(dt.fullyear);
            Integers.Add(dt.billion);
            Integers.Add(dt.million);
            Integers.Add(dt.year);
            Integers.Add(dt.DayOfYear);
            Integers.Add(dt.Month);
            Integers.Add(dt.Day);
            Integers.Add(dt.Hour);
            Integers.Add(dt.Minute);
            Integers.Add(dt.Second);
            Integers.Add(dt.Milliseconds);
            //Integers.Add(dt.Ticks);
            string month = dt.MonthName;
            string WeekDay = dt.WeekDay;
            Console.WriteLine(DateTime.Now.TimeOfDay);
            Time t = dt.TimeOfDay;
            Integers.Add(t.Days);
            Integers.Add(t.Hours);
            Integers.Add(t.Minutes);
            Integers.Add(t.Seconds);
            Integers.Add(t.Milliseconds);
            //Integers.Add(t._ticks);
            // Get current DateTime. It can be any DateTime object in your code.  
            DateTime aDate = DateTime.Now;
            StarDate bDate = StarDate.Now;


            // Format Datetime in different formats and display them  
            Console.WriteLine(("MM/dd/yyyy")); Console.WriteLine(aDate.ToString("MM/dd/yyyy")); Console.WriteLine(bDate.ToString("MM/dd/yyyy"));
            Console.WriteLine(("dddd, dd MMMM yyyy")); Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(("dddd, dd MMMM yyyy")); Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(("dddd, dd MMMM yyyy")); Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(("dddd, dd MMMM yyyy")); Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(("dddd, dd MMMM yyyy")); Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy")); Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy"));
            Console.WriteLine(("dddd, dd MMMM yyyy HH:mm:ss")); Console.WriteLine(aDate.ToString("dddd, dd MMMM yyyy HH:mm:ss")); Console.WriteLine(bDate.ToString("dddd, dd MMMM yyyy HH:mm:ss"));
            Console.WriteLine(("MM/dd/yyyy HH:mm")); Console.WriteLine(aDate.ToString("MM/dd/yyyy HH:mm")); Console.WriteLine(bDate.ToString("MM/dd/yyyy HH:mm"));
            Console.WriteLine(("MM/dd/yyyy hh:mm tt")); Console.WriteLine(aDate.ToString("MM/dd/yyyy hh:mm tt")); Console.WriteLine(bDate.ToString("MM/dd/yyyy hh:mm tt"));
            Console.WriteLine(("MM/dd/yyyy H:mm")); Console.WriteLine(aDate.ToString("MM/dd/yyyy H:mm")); Console.WriteLine(bDate.ToString("MM/dd/yyyy H:mm"));
            Console.WriteLine(("MM/dd/yyyy h:mm tt")); Console.WriteLine(aDate.ToString("MM/dd/yyyy h:mm tt")); Console.WriteLine(bDate.ToString("MM/dd/yyyy h:mm tt"));
            Console.WriteLine(("MM/dd/yyyy HH:mm:ss")); Console.WriteLine(aDate.ToString("MM/dd/yyyy HH:mm:ss")); Console.WriteLine(bDate.ToString("MM/dd/yyyy HH:mm:ss"));
            Console.WriteLine(("MMMM dd")); Console.WriteLine(aDate.ToString("MMMM dd")); Console.WriteLine(bDate.ToString("MMMM dd"));
            Console.WriteLine(("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss.fffffffK")); Console.WriteLine(aDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss.fffffffK")); Console.WriteLine(bDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss.fffffffK"));
            Console.WriteLine(("ddd, dd MMM yyy HH’:’mm’:’ss ‘GMT’")); Console.WriteLine(aDate.ToString("ddd, dd MMM yyy HH’:’mm’:’ss ‘GMT’")); Console.WriteLine(bDate.ToString("ddd, dd MMM yyy HH’:’mm’:’ss ‘GMT’"));
            Console.WriteLine(("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss")); Console.WriteLine(aDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss")); Console.WriteLine(bDate.ToString("yyyy’-‘MM’-‘dd’T’HH’:’mm’:’ss"));
            Console.WriteLine(("HH:mm")); Console.WriteLine(aDate.ToString("HH:mm")); Console.WriteLine(bDate.ToString("HH:mm"));
            Console.WriteLine(("hh:mm tt")); Console.WriteLine(aDate.ToString("hh:mm tt")); Console.WriteLine(bDate.ToString("hh:mm tt"));
            Console.WriteLine(("H:mm")); Console.WriteLine(aDate.ToString("H:mm")); Console.WriteLine(bDate.ToString("H:mm"));
            Console.WriteLine(("h:mm tt")); Console.WriteLine(aDate.ToString("h:mm tt")); Console.WriteLine(bDate.ToString("h:mm tt"));
            Console.WriteLine(("HH:mm:ss")); Console.WriteLine(aDate.ToString("HH:mm:ss")); Console.WriteLine(bDate.ToString("HH:mm:ss"));
            Console.WriteLine(("yyyy MMMM")); Console.WriteLine(aDate.ToString("yyyy MMMM")); Console.WriteLine(bDate.ToString("yyyy MMMM"));
            Dictionary<string, Time> times = new Dictionary<string, Time>();
            //StarDate dt = StarDate.UtcNow;
            times.Add("atomic", dt.atomic);
            times.Add("radio", dt.Radio);
            times.Add("terra", dt.Terra);
            times.Add("arrival", dt.Arrival);

            StarZone z = StarZone.Local;
            Time timeSpanInfo = z.BaseUtcOffset;
            timeSpanInfo = z.Offset(StarDate.Now);
            string daylightname = z.DaylightName;
            string s = z.DisplayName;
            s = z.Id;
            s = z.StandardName;
            bool SupportsDaylightSavingTime = z.SupportsDaylightSavingTime;
            z.ClearCachedData();
            StarZone.ConvertTime(StarDate.Now, StarZone.UTC);
            StarZone.ConvertTime(StarDate.Now, StarZone.Local, StarZone.UTC);
            StarZone.ConvertTimeBySystemTimeZoneId(StarDate.Now, "string");
            StarZone.ConvertTimeBySystemTimeZoneId(StarDate.Now, "StarZone.Local", "StarZone.UTC");
            dt = StarZone.ConvertTimeToUtc(dt);
            dt = StarZone.ConvertTimeToUtc(dt, z);
            z = StarZone.FindSystemTimeZoneById("string");
            z = StarZone.FromSerializedString("string");
            TimeZoneInfo.AdjustmentRule[] adjustmentRules = z.GetAdjustmentRules();
            StarZone[] GetSystemTimeZones = StarZone.GetSystemTimeZones();
            bool HasSameRules = z.HasSameRules(StarZone.Local);
            bool b = z.IsDaylightSavingTime(dt);
            s = z.ToSerializedString();
            s = z.ToString("overload");
        }
    }
}
