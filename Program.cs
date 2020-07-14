using StarCalendar;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using System.Runtime.Serialization;
using System.Security.Cryptography.X509Certificates;

namespace ConsoleApp
{
    class Program
    {
        //private static object Integers;

        static void Main(string[] args)
        {
            StarZone local = StarZone.Local;
            StarDate dt = StarDate.Now;
            StarDate.LongDefault = false;
            Console.WriteLine(dt.TickTimeZoneConvert(StarZone.UTC));
            var error = dt.error;
            print(StarDate.StarHanukkah());
            StarDate.MakeChart("");
            StarDate.MakeChart("", 2020);
            print(StarDate.StarHanukkah(DateTime.Now));
            print(StarDate.StarHanukkah(StarDate.Now));
            print(StarDate.TryParse("lol", out dt));
            print(StarDate.GregHanukkah());
            print(StarDate.GregHanukkah(DateTime.Now));
            print(StarDate.GregHanukkah(StarDate.Now));
            print(dt.fullyear);
            print(dt.quadrillion);
            print(dt.trillion);
            print(dt.billion);
            print(dt.million);
            print(dt.Radio);
            print(dt.Terra);
            print(dt.IsTerran);
            print(dt.Arrival);
            print(dt.SupportsDaylightSavingTime);
            print(dt.offset);
            print(new StarDate(new DateTime(2010, 01, 05)));
            print(dt.EasterDate());
            print(StarDate.StarEaster(2020));
            print(StarDate.StarThanksgiving(2020));
            print(dt.Easter());
            //print(StarDate.Today);
            print(dt.Today);
            print(dt.gregyear());
            //print(StarDate.FromGreg(2010, 05, 01, 01, 01, 01, 01, 01));
            print(StarDate.GregThanksgiving(2010));
            print(StarDate.GregEaster(1950));
            print(dt.CompareTo(StarDate.Manu));
            print(dt.Equals(StarDate.Maya));
            StarDate m = StarDate.Manu;
            print(m + StarDate.DayTime);
            print(dt++);
            print(++dt);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt++);
            print(dt--);
            print(StarDate.FromGreg(1));
            print(StarDate.FromGreg(1, 1));
            print(StarDate.FromGreg(1, 1, 1));
            print(StarDate.FromGreg(1, 1, 1, 1));
            print(StarDate.FromGreg(1, 1, 1, 1, 1));
            print(StarDate.FromGreg(1, 1, 1, 1, 1, 1));
            print(StarDate.FromGreg(1, 1, 1, 1, 1, 1, 1));
            print(StarDate.Between(StarDate.Manu, StarDate.Now));
            print(dt.DateTime);
            dt -= StarDate.YearTime;
            print(dt);
            StarDate b = StarDate.Between(StarDate.Manu, dt);
            print(dt == b);
            print(dt != b);
            print(dt < b);
            print(dt > b);
            print(dt.ToString());
            print(dt.addtime("1 hour"));
            print(dt.isleapyear());
            print(dt.isDoubleLeapYear());
            print(StarDate.isleapyear(4000));
            print(dt.GregNumbers());
            print(StarDate.GregChineseNewYear());
            print(StarDate.GregChineseNewYear(DateTime.Now));
            print(StarDate.GregChineseNewYear(dt));
            print(StarDate.StarPurim());
            print(StarDate.StarPurim(dt.DateTime));
            print(StarDate.StarPurim(dt));
            print(StarDate.GregPurim());
            print(StarDate.GregPurim(dt.DateTime));
            print(StarDate.GregPurim(dt));
            print(dt);
            print(dt.DateTime);
            print(new StarDate(new BigInteger(10000000000000), DateTimeKind.Local));
            print(new StarDate(new BigInteger(10000000000000), DateTimeKind.Local, false));
            print(dt.Add(StarDate.YearTime));
            print(dt.Add(new TimeSpan(5000000)));
            print(dt.AddTicks(500));
            print(dt.AddDays(500));
            print(dt.AddHours(50));
            print(dt.AddMilliseconds(900000));
            print(dt.AddMinutes(60));
            print(dt.AddMonths(50));
            print(dt.AddTicks(5000));
            print(StarDate.Compare(dt, m));
            //print(dt.CompareTo(c));
            print(dt.CompareTo(m));
            print(dt.Equals(m));
            print(dt.Equals(m));
            print(StarDate.Equals(dt, m));
            print(StarDate.FromBinary(111555));
            print(dt.IsDaylightSavingTime());
            print(StarDate.SpecifyKind(dt, DateTimeKind.Utc));
            print(dt.ToBinary());
            print(dt.Date);
            print(dt.Day);
            print(dt.DayOfWeek);
            print(dt.DayOfYear);
            print(dt.GetHashCode());
            print(dt.Hour);
            print(dt.Kind);
            print(dt.Minute);
            print(dt.Month);
            print(StarDate.Now);
            print(StarDate.UtcNow);
            print(dt.Julian);
            print(StarDate.NetStart);
            print(dt.ChristNet);
            print(dt.atomic);
            print(dt.TicksPerLocalDay);
            print(dt.LocalDay);
            //print(StarDate.DefaultFormat);
            print(dt.ExtraTicks);
            print(StarDate.Maya);
            print(dt.TimeZone);
            print(StarDate.IsGregLeapYear(2020));
            print(StarDate.Parse("Aquarius 1st 12020"));
            //print(StarDate.Parse("Aquarius 1st 12020", StarCulture.InvariantCulture.FormatProvider));
            //print(StarDate.ParseExact("Aquarius 1st 2020", "MMMMMMM, dddddd, yyyyyyy", /*StarCulture*/.InvariantCulture.FormatProvider));
            print(dt.Subtract(StarDate.Maya));
            print(dt.Subtract(StarDate.YearTime));
            print(dt.Subtract(new DateTime(2020, 01, 05)));
            print(dt.ToOADate());
            print(dt.ToFileTime());
            print(dt.ToFileTimeUtc());
            print(dt.ToLocalTime());
            print(dt.ToLocalTime(true));
            print(dt.ToZone(StarDate.UTC));
            print(dt.ToLongDateString());
            print(dt.ToLongDateString());
            print(dt.ToLongTimeString());
            print(dt.ToShortDateString());
            print(dt.ToShortTimeString());
            print(dt.ToUniversalTime());
            StarDate star;
            print(StarDate.TryParse("Aquarius 5th 12019", out star));
            //print(dt.GetStarDateFormats());
            //print(dt.GetStarDateFormats(StarCulture.InvariantCulture.FormatProvider));
            //print(dt.GetStarDateFormats('D'));
            //print(dt.GetStarDateFormats('D', StarCulture.InvariantCulture.FormatProvider));
            //print(dt.GetTypeCode());
            print(dt.CompareTo(DateTime.Now));
            print(dt.Equals(DateTime.Now));
            print(new StarDate(5000000000000, 5000000000000, DateTimeKind.Utc));// : this(ticks)
            StarZone z = StarZone.Local;
            print(StarZone.Local);
            print(StarZone.Terra);
            print(StarZone.Mars);
            print(StarZone.Amaterasu);
            print(StarZone.UTC);
            print(z.hasTimeZone);
            print(z.hasTimeZone);
            print(z.IsTerran);
            print(z.Day);
            print(z.DaylightName);
            print(z.DisplayName);
            print(z.StandardName);
            print(z.SupportsDaylightSavingTime);
            print(z.distance());
            print(StarZone.GetSystemStarZones());
            print(StarZone.ConvertTime(dt, StarZone.Local, StarZone.UTC));
        }

        public static void print(object v)
        {
            Console.WriteLine(v);
        }

        public static void print(object[] vs)
        {
            try
            {
                foreach (var entry in vs)
                {
                    Console.WriteLine(entry);
                }
            }
            catch (NullReferenceException)
            {
                int i = 0;
                while (i < vs.Length)
                {
                    Console.WriteLine(vs[i++]);
                }
            }
        }
    }
}
