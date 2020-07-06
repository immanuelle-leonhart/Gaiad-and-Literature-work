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
            long bi = 14000000000;
            Console.WriteLine(bi);
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

            Zone z = Zone.Local;
            TimeSpanInfo timeSpanInfo = z.BaseUtcOffset;
            timeSpanInfo = z.GetOffset(StarDate.Now);
            string daylightname = z.DaylightName;
            string s = z.DisplayName;
            s = z.Id;
            s = z.StandardName;
            bool SupportsDaylightSavingTime = z.SupportsDaylightSavingTime;
            z.ClearCachedData();
            Zone.ConvertTime(StarDate.Now, Zone.UTC);
            Zone.ConvertTime(StarDate.Now, Zone.Local, Zone.UTC);
            Zone.ConvertTimeBySystemTimeZoneId(StarDate.Now, "string");
            Zone.ConvertTimeBySystemTimeZoneId(StarDate.Now, "Zone.Local", "Zone.UTC");
            dt = Zone.ConvertTimeToUtc(dt);
            dt = Zone.ConvertTimeToUtc(dt, z);
            z = Zone.FindSystemTimeZoneById("string");
            z = Zone.FromSerializedString("string");
            TimeZoneInfo.AdjustmentRule[] adjustmentRules = z.GetAdjustmentRules();
            Zone[] GetSystemTimeZones = Zone.GetSystemTimeZones();
            bool HasSameRules = z.HasSameRules(Zone.Local);
            bool b = z.IsDaylightSavingTime(dt);
            s = z.ToSerializedString();
            s = z.ToString("overload");
        }
    }
}
