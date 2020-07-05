//using Consul;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data.SqlTypes;
using System.Diagnostics.CodeAnalysis;
using System.Diagnostics.SymbolStore;
using System.Globalization;
using System.IO;
using System.Net;
using System.Numerics;
using System.Reflection.Metadata.Ecma335;
using System.Runtime.CompilerServices;

namespace StarCalendar
{
    public struct StarDate : IComparable<StarDate>, IEquatable<StarDate>
    {
        public TimeSpanInfo atomic;
        private StarData metadata;
        //private bool isTerran;
        //private bool complexTimeZone;
        //private bool hasTimeZone;

        //private TimeSpanInfo radio;
        //private TimeSpanInfo terra;
        //private TimeSpanInfo arrival;

        internal static int DayFromMonth(int day)
        {
            day--;
            day %= 7;
            day++;
            return day;
        }

        public static StarDate StarHanukkah()
        {
            return new StarDate(GregHanukkah());
        }

        private static void DemonstrateLanguage(CultureInfo lang, string format)
        {
            //StarDate.SetFormat("numeric");
            StarDate dt = c.maya;
            dt -= 379 * c.Day;
            int i = 0;
            while (dt < c.maya)
            {
                dt += c.Day;
                i++;
                Console.WriteLine(dt.ToString(lang, format));
            }
        }

        internal static void SetFormat(string v)
        {
            d.format = v;
        }

        public static void MakeChart(string v)
        {
            StarDate.MakeChart(v, DateTime.Now.Year);
        }

        public static void MakeChart(string v, int gregyear)
        {
            StreamWriter chart = new StreamWriter(v + "StarCalendar.csv");
            StarDate dt = StarDate.FromGreg(gregyear, 6, 1);
            long staryear = dt.year;
            dt = new StarDate(staryear, 1, 1);
            StarDate end = StarDate.FromGreg(gregyear + 1, 1, 1);
            string gregday = "Day of the Gregorian Month";
            string gregmonthname = "Gregorian Month Name";
            string gregmonthnumber = "Gregorian Month Number";
            string g_year = "Gregorian Year";
            string gregdayofyear = "Gregorian Day of Year";
            string weekday = "Day of the Week";
            string comma = ",";
            string starday = "Day of the Star Month";
            string starmonthname = "Star Month Name";
            string starmonthnumber = "Star Month Number";
            string StarYear = "Star Year";
            string Stardayofyear = "Star Day of Year";
            string[] months = new string[] { "None", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" };
            string output = g_year + comma + gregmonthname + comma + gregmonthnumber + comma + gregday + comma + gregdayofyear + comma + weekday + comma + StarYear + comma + starmonthname + comma + starmonthnumber + comma + starday + comma + Stardayofyear;
            while (dt <= end)
            {
                Console.WriteLine(output);
                chart.WriteLine(output);
                DateTime g = dt.Convert();
                gregday = g.Day.ToString();
                gregmonthname = months[g.Month];
                gregmonthnumber = g.Month.ToString();
                g_year = g.Year.ToString();
                gregdayofyear = g.DayOfYear.ToString();
                weekday = g.DayOfWeek.ToString();
                starday = dt.day.ToString();
                starmonthname = dt.MonthName;
                starmonthnumber = dt.Month.ToString();
                StarYear = dt.year.ToString();
                Stardayofyear = dt.DayOfYear.ToString();
                output = g_year + comma + gregmonthname + comma + gregmonthnumber + comma + gregday + comma + gregdayofyear + comma + weekday + comma + StarYear + comma + starmonthname + comma + starmonthnumber + comma + starday + comma + Stardayofyear;
                dt += c.Day;
            }
            chart.Flush();
            chart.Close();
        }

        internal static StarDate AbstractDate(TimeSpanInfo timeSpanInfo)
        {
            StarDate dt = new StarDate(timeSpanInfo);
            dt.metadata = StarData.Local;
            return dt;
        }

        internal static string Time(Dictionary<string, int> data)
        {
            string dt = "";
            try
            {
                dt = data["hour"] + ":" + data["min"];
                try
                {
                    dt = dt + ":" + data["second"];
                    try
                    {
                        dt = dt + ":" + data["Milliseconds"];
                        try
                        {
                            dt = dt + ":" + data["ticks"];
                        }
                        catch (KeyNotFoundException)
                        {

                        }
                    }
                    catch (KeyNotFoundException)
                    {

                    }
                }
                catch (KeyNotFoundException)
                {

                }
            }
            catch (KeyNotFoundException)
            {

            }
            return dt;
        }

        private static string GregHoliday(DateTime dateTime)
        {
            throw new NotImplementedException();
        }

        public static StarDate StarHanukkah(DateTime dt)
        {
            return new StarDate(GregHanukkah(dt));
        }

        public static StarDate StarHanukkah(StarDate dt)
        {
            return new StarDate(GregHanukkah(dt));
        }

        internal static StarDate Parse(string v)
        {
            throw new NotImplementedException();
        }

        public static DateTime GregHanukkah()
        {
            return GregHanukkah(DateTime.Now);
        }

        public static DateTime GregHanukkah(DateTime now)
        {
            Calendar HebCal = new HebrewCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 11, 1);
            int hebyear = HebCal.GetYear(now);
            DateTime Hanukkah = new DateTime(hebyear, 3, 25, new HebrewCalendar());
            return Hanukkah;
        }

        public static DateTime GregHanukkah(StarDate dt)
        {
            DateTime o = new StarDate(dt.year, 12, 1).Convert();
            return GregHanukkah(o);
        }



        //public Zone timeZone;


        internal static StarDate MathFromGreg(int[] v)
        {
            return MathFromGreg(v[0], v[1], v[2]);
        }






        public int Hour
        {
            get
            {
                return this.LocalData()["hour"];
            }
            internal set
            {
                int h = value;
                int diff = h - this.Hour;
                this.atomic += diff * c.Hour;
            }
        }
        public int Minute
        {
            get { return this.LocalData()["minute"]; }
            internal set
            {
                int h = value;
                int diff = h - this.Minute;
                this.atomic += diff * c.Minute;
            }
        }
        public int Second
        {
            get { return this.LocalData()["second"]; }
            internal set
            {
                int diff = value - this.Second;
                this.atomic += diff * c.Second;
            }
        }

        public static StarDate Now
        {
            get { return new StarDate(DateTime.UtcNow); }
            //internal set
            //{
            //    now = value;
            //}
        }
        public static StarDate UtcNow
        {
            get
            {
                return new StarDate(DateTime.UtcNow, StarData.Local);
            }
        }
        public long fullyear
        {
            get { return this.atomic / c.AverageYear; }
            internal set
            {
                long diff = value - this.fullyear;
                this.atomic += diff * c.AverageYear;
            }
        }
        public int billion
        {
            get { return this.atomic / c.b; }
            internal set
            {
                int diff = value - this.billion;
                this.atomic += diff * c.b;
            }
        }
        public int million
        {
            get
            {
                TimeSpanInfo t = this.atomic % c.b;
                return t / c.m;
            }
            internal set
            {
                int diff = value - this.million;
                this.atomic += diff * c.m;
            }
        }
        public int year
        {
            get { return LocalData("year")["year"]; }
            internal set
            {
                int[] vs = this.values();
                vs[2] = value;
                StarDate dt = CosmicDate(vs);
                this.atomic = dt.atomic;
                //throw new NotImplementedException(lololololol);
            }
        }

        private StarDate CosmicDate(int[] vs)
        {
            throw new NotImplementedException();
        }

        private int[] values()
        {
            throw new NotImplementedException();
        }

        public int Month
        {
            get { return LocalData("Month")["Month"]; }
            internal set
            {
                int diff = value - this.Month;
                this.atomic += diff * c.month;
            }
        }
        public int day
        {
            get { return LocalData("day")["day"]; }
            internal set
            {
                int diff = value - this.day;
                this.atomic += diff * c.Day;
            }
        }
        public int Milliseconds
        {
            get { return LocalData()["Milliseconds"]; }
            internal set
            {
                int diff = value - this.Milliseconds;
                this.atomic += diff * c.Millisecond;
            }
        }
        public BigInteger Ticks
        {
            get { return this.atomic.ticks; }
            internal set
            {
                this.atomic.ticks = value;
            }
        }
        public string MonthName
        {
            get { return this.GetMonthName(this.Month, d.getlocale()); }
            internal set
            {
                switch (value)
                {
                    case "Sagittarius":
                        this.Month = 1;
                        break;
                    case "Capricorn":
                        this.Month = 2;
                        break;
                    case "Aquarius":
                        this.Month = 3;
                        break;
                    case "Pisces":
                        this.Month = 4;
                        break;
                    case "Aries":
                        this.Month = 5;
                        break;
                    case "Taurus":
                        this.Month = 6;
                        break;
                    case "Gemini":
                        this.Month = 7;
                        break;
                    case "Karkino":
                        this.Month = 8;
                        break;
                    case "Leo":
                        this.Month = 9;
                        break;
                    case "Virgo":
                        this.Month = 10;
                        break;
                    case "Libra":
                        this.Month = 11;
                        break;
                    case "Scorpio":
                        this.Month = 12;
                        break;
                    case "Ophiuchus":
                        this.Month = 13;
                        break;
                    case "Horus":
                        this.Month = 14;
                        break;
                    default:
                        break;
                }
            }
        }

        private int MonthNumberFromName(string value)
        {
            throw new NotImplementedException();
        }

        private string GetMonthName(int month, CultureInfo locale)
        {
            throw new NotImplementedException();
        }

        public string WeekDay
        {
            get { return this.GetWeekDayName(this.WeekInt, d.getlocale()); }
            internal set
            {
                switch (value)
                {
                    case "Monday":
                        this.WeekInt = 1;
                        break;
                    case "Tuesday":
                        this.WeekInt = 2;
                        break;
                    case "Wednesday":
                        this.WeekInt = 3;
                        break;
                    case "Thursday":
                        this.WeekInt = 4;
                        break;
                    case "Friday":
                        this.WeekInt = 5;
                        break;
                    case "Saturday":
                        this.WeekInt = 6;
                        break;
                    case "Sunday":
                        this.WeekInt = 7;
                        break;
                    default:
                        break;
                }
            }
        }

        private string GetWeekDayName(int weekInt, CultureInfo locale)
        {
            throw new NotImplementedException();
        }

        public TimeSpanInfo TimeOfDay
        {
            get { return this.atomic % c.Day; }
            internal set
            {
                TimeSpanInfo diff = value - this.TimeOfDay;
                this.atomic += diff;
            }
        }

        public int DayOfYear
        {
            get { return LocalData()["day of year"]; }
            internal set
            {
                int diff = value - this.DayOfYear;
                this.atomic += diff * c.Day;
            }
        }
        public TimeSpanInfo error
        {
            get
            {
                return this.metadata.error;
            }

            private set
            {
                this.metadata.error = value;
            }
        }

        public string Note
        {
            get
            {
                return this.metadata.note;
            }

            private set
            {
                this.metadata.note = value;
            }
        }

        public int WeekInt
        {
            get { return StarDate.DayFromMonth(this.day); }
            private set
            {
                int diff = value - this.WeekInt;
                this.atomic += diff * c.Day;
            }
        }

        public Zone TimeZone
        {
            get
            {
                try
                {
                    return this.metadata.timeZone;
                }
                catch (NullReferenceException)
                {
                    this.metadata = StarData.Local;
                    return c.UTC;
                }
            }
            private set
            {
                this.metadata.timeZone = value;
            }
        }

        public TimeSpanInfo Radio
        {
            get
            {
                return this.TimeZone.ToRadio(this.atomic);
            }

            internal set
            {
                this.atomic = this.TimeZone.FromRadio(value);
            }
        }
        public TimeSpanInfo Terra
        {
            get
            {
                return this.TimeZone.ToTerran(this.atomic);
            }

            internal set
            {
                this.atomic = this.TimeZone.FromTerran(value);
            }
        }
        public TimeSpanInfo Arrival
        {
            get
            {
                return this.TimeZone.ToArrival(this.atomic);
            }

            internal set
            {
                this.atomic = this.TimeZone.FromArrival(value);
            }
        }

        public bool IsTerran
        {
            get
            {
                return this.metadata.IsTerran;
            }
        }
        public bool ComplexTimeZone
        {
            get
            {
                return this.metadata.ComplexTimeZone;
            }

        }
        public bool HasTimeZone
        {
            get
            {
                return this.metadata.HasTimeZone;
            }

        }

        public StarDate(DateTime utcNow)
        {
            this.atomic = c.netstart.atomic + new TimeSpanInfo(utcNow.Ticks);

            //this.error = new TimeSpanInfo(0);
            this.metadata = StarData.Standard;
            //this.timeZone = Zone.Here();
            //this.Note = "";
        }

        public StarDate EasterDate()
        {
            return StarEaster((int)this.gregyear());
        }

        internal static StarDate StarEaster(int year)
        {
            DateTime easter = StarDate.GregEaster(year);
            return new StarDate(easter);
        }

        internal static StarDate StarThanksgiving(int year)
        {
            DateTime Thanksgiving = StarDate.GregThanksgiving(year);
            return new StarDate(Thanksgiving);
        }



        internal bool Easter()
        {
            return this.today() == this.EasterDate();
        }

        private StarDate today()
        {
            throw new NotImplementedException();
        }

        internal static StarDate MathFromGreg(int v1, int v2, int v3)
        {
            return MathFromGreg(v1, v2, v3, 0, 0, 0, 0);
        }

        //internal string Stored()
        //{
        //    return this.year + "-" + this.Month() + "-" + this.day();
        //}

        internal static StarDate GregParse(string[] data)
        {
            throw new NotImplementedException();
        }

        internal void AddTime(string[] data)
        {
            throw new NotImplementedException();
        }

        //    internal string teststring()
        //    {
        //        //if (this == c.netstart)
        //        //{
        //        //    return new int[] { 1, 1, 1 };
        //        //}
        //        //else
        //        //{
        //            TimeSpanInfo t = this - c.netstart;
        //            int DaysPerYear = 365;
        //            // Number of days in 4 years
        //            int DaysPer4Years = DaysPerYear * 4 + 1;       // 1461
        //                                                           // Number of days in 100 years
        //            int DaysPer100Years = DaysPer4Years * 25 - 1;  // 36524
        //                                                           // Number of days in 400 years
        //            int DaysPer400Years = DaysPer100Years * 4 + 1; // 146097
        //                                                           //TimeSpanInfo q = DaysPer400Years * c.Day;
        //                                                           //TimeSpanInfo s = DaysPer100Years * c.Day;
        //                                                           //TimeSpanInfo l = DaysPer4Years * c.Day;
        //                                                           //TimeSpanInfo y = DaysPerYear * c.Day;
        //            int[] DaysToMonth365 = {
        //                0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
        //            int[] DaysToMonth366 = {
        //                0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};

        //            //Console.WriteLine("testing");

        //            //Console.WriteLine(t);

        //            int days = t / c.Day;
        //            //Console.WriteLine("days from netstart = " + days);

        //            int q = days / DaysPer400Years;
        //            int qmod = days % DaysPer400Years;
        //            //Console.WriteLine(q);
        //            //Console.WriteLine(qmod);
        //            if (qmod < 0)
        //            {
        //                qmod = DaysPer400Years + qmod;
        //                q--;
        //            }
        //            //Console.WriteLine(q);
        //            //Console.WriteLine(qmod);
        //            int s = qmod / DaysPer100Years;
        //            int smod = qmod % DaysPer100Years;
        //            int l = smod / DaysPer4Years;
        //            int lmod = smod % DaysPer4Years;
        //            int y = lmod / DaysPerYear;
        //            int ymod = lmod % DaysPerYear;
        //            //Console.WriteLine(s);
        //            //Console.WriteLine(l);
        //            //Console.WriteLine(y);
        //            int m = 500;
        //            int yd = ymod;
        //            int d = 500;
        //            int year = 400 * q + 100 * s + 4 * l + y;
        //            //if (year < 1)
        //            //{
        //            //    year--;
        //            //}
        //            if (s == 4)
        //            {
        //                s = 3;
        //                l = 24;
        //                y = 3;
        //                m = 11;
        //                d = 31;
        //                year--;
        //            }
        //            else if (GregLeap(year) == true)
        //            {
        //                int i = 0;
        //                bool found = false;
        //                while (!found)
        //                {
        //                    //Console.WriteLine(DaysToMonth366[i]);
        //                    if (DaysToMonth366[i] > yd)
        //                    {
        //                        m = i - 1;
        //                        found = true;
        //                        d = yd - DaysToMonth366[m] + 1;
        //                    }
        //                    else
        //                    {
        //                        i++;
        //                    }
        //                }
        //            }
        //            else
        //            {
        //                //Console.WriteLine(GregLeap(year));
        //                int i = 0;
        //                bool found = false;
        //                while (!found)
        //                {
        //                    //Console.WriteLine(DaysToMonth366[i]);
        //                    if (DaysToMonth365[i] > yd)
        //                    {
        //                        m = i - 1;
        //                        found = true;
        //                        d = yd - DaysToMonth365[m] + 1;
        //                    }
        //                    else
        //                    {
        //                        i++;
        //                    }
        //                }
        //            }
        //        //Console.WriteLine(year + " " + m + " " + d + " ");
        //        //throw new NotImplementedException();
        //        if (this > c.netstart)
        //        {
        //            Console.WriteLine("TEST");
        //            year++;
        //        }
        //        m++;
        //            int[] vs = new int[] { year, m, d };
        //        return year + "-" + m + "-" + d;


        //}

        private long gregyear()
        {
            if (this.year > 10000)
            {
                return this.year - 10000;
            }
            else
            {
                return this.year - 10001;
            }
        }

        public static DateTime GregThanksgiving(int year)
        {
            DateTime dt = new DateTime(year, 11, 1);
            while (dt.DayOfWeek.ToString() != "Thursday")
            {
                dt = dt.AddDays(1);
            }
            return dt.AddDays(21);
        }

        public static DateTime GregEaster(int year)
        {
            int a = year % 19;
            int b = year / 100;
            int c = (b - (b / 4) - ((8 * b + 13) / 25) + (19 * a) + 15) % 30;
            int d = c - (c / 28) * (1 - (c / 28) * (29 / (c + 1)) * ((21 - a) / 11));
            int e = d - ((year + (year / 4) + d + 2 - b + (b / 4)) % 7);
            int month = 3 + ((e + 40) / 44);
            int day = e + 28 - (31 * (month / 4));
            return new DateTime(year, month, day);
        }

        public StarDate(TimeSpanInfo t) : this()
        {
            this.atomic = t;
            this.metadata = StarData.Local;
        }

        public StarDate(int v) : this()
        {
            this.atomic = new TimeSpanInfo(v);
            this.metadata = StarData.Local;
        }

        public StarDate(int v, Zone Zone) : this(v)
        {
            this.atomic = new TimeSpanInfo(v) + c.netstart.atomic;
            this.metadata = new StarData(Zone);
        }

        //internal long DayOfYear()
        //{
        //    return this.LocalData()["day of year"];
        //}

        //public StarDate(DateTime utcNow, Zone zone) : this(utcNow)
        //{
        //    this.atomic = new TimeSpanInfo(v) + c.netstart.atomic;
        //}

        public StarDate(DateTime utcNow, Zone zone) : this(utcNow)
        {
            this.atomic = c.netstart.atomic + new TimeSpanInfo(utcNow.Ticks);
            this.metadata = new StarData(zone);
        }

        private static StarDate AnnoCosmos(params long[] vs)
        {
            throw new NotImplementedException();
            //long[] data = new long[] { 0, 0, 0, 0, 0, 0, 0, 0 };
            //int i = 0;
            //int n = vs.Length;
            //if (n > 8)
            //{
            //    n = 8;
            //}
            //while (i < n)
            //{
            //    data[i] = vs[i];
            //    i++;
            //}
            //this.atomic = new TimeSpanInfo(0);
            //long years = data[0];
            //long cycle_78 = years / 78;
            //this.atomic += cycle_78 * c.Seventy_Eight;
            //years %= 78;
            //long cycle_6 = years / 6;
            //this.atomic += cycle_6 * c.Sixyear;
            //years %= 6;
            //long cycle_1 = years;
            //this.atomic += cycle_1 * c.Year;
            //data[1]--;
            //data[2]--; //The 1st of a Month is actually zero days, so subtract one from the day, same for months
            //this.atomic += data[1] * c.Month + data[2] * c.Day + data[3] * c.Hour + data[4] * c.Minute + data[5] * c.Second + data[6] * c.Millisecond + new TimeSpanInfo(data[7]);
            //switch (n)
            //{
            //    case 1:
            //        this.error = c.Year;
            //        break;
            //    case 2:
            //        this.error = c.Month;
            //        break;
            //    case 3:
            //        this.error = c.Day;
            //        break;
            //    case 4:
            //        this.error = c.Hour;
            //        break;
            //    case 5:
            //        this.error = c.Minute;
            //        break;
            //    case 6:
            //        this.error = c.Second;
            //        break;
            //    case 7:
            //        this.error = c.Millisecond;
            //        break;
            //    case 8:
            //    default:
            //        this.error = new TimeSpanInfo(0);
            //        break;
            //}

            ////assign timezones

            //this.timeZone = c.UTC;

            ////assign notes

            //this.note = "";
        }


        public StarDate(params long[] vs)
        {
            long[] data = new long[] { 0, 0, 0, 0, 0, 0, 0, 0 };
            int i = 0;
            int n = vs.Length;
            if (n > 8)
            {
                n = 8;
            }
            while (i < n)
            {
                data[i] = vs[i];
                i++;
            }
            //this = c.manu;
            this.atomic = new TimeSpanInfo(0);
            this.atomic += 14 * c.b;
            long years = data[0];
            long cycle_78 = years / 78;
            this.atomic += cycle_78 * c.Seventy_Eight;
            years %= 78;
            long cycle_6 = years / 6;
            this.atomic += cycle_6 * c.Sixyear;
            years %= 6;
            long cycle_1 = years;
            this.atomic += cycle_1 * c.Year;
            data[1]--;
            data[2]--; //The 1st of a Month is actually zero days, so subtract one from the day, same for months
            this.atomic += data[1] * c.month + data[2] * c.Day + data[3] * c.Hour + data[4] * c.Minute + data[5] * c.Second + data[6] * c.Millisecond + new TimeSpanInfo(data[7]);


            metadata = new StarData(n);
        }

        public StarDate(TimeSpanInfo t, Zone uTC) : this(t)
        {
            this.atomic = t;
            this.metadata = new StarData(uTC);
        }

        internal StarDate(DateTime utcNow, StarData local) : this(utcNow)
        {
            //this.atomic = utcNow;
            this.metadata = local;
        }

        //public static StarDate Now()
        //{
        //    return new StarDate(DateTime.UtcNow);
        //}

        //public static StarDate UTCNow()
        //{
        //    return new StarDate(DateTime.UtcNow, c.UTC);
        //}

        int IComparable<StarDate>.CompareTo(StarDate other)
        {
            throw new NotImplementedException();
        }

        bool IEquatable<StarDate>.Equals(StarDate other)
        {
            throw new NotImplementedException();
        }

        public static StarDate operator +(StarDate d, TimeSpanInfo t)
        {
            StarDate dt = d;
            dt.atomic += t;
            return dt;
        }

        public static StarDate GregParse(string input)
        {
            DateTime dt;
            try
            {
                dt = DateTime.Parse(input);
                return new StarDate(dt);
            }
            catch (System.FormatException)
            {
                string[] parsedinput = input.Split(' ');
                string modifier = parsedinput[0];
                if (modifier == "Star")
                {
                    //long year = long.Parse(parsedinput[1]);
                    //int Month = int.Parse(parsedinput[2]);
                    //int day = int.Parse(parsedinput[3]);
                    int i = 1;
                    long[] vs = new long[] { 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
                    while (i < parsedinput.Length)
                    {
                        vs[i - 1] = long.Parse(parsedinput[i]);
                        i++;
                    }
                    return AnnoCosmos(vs);
                    //new StarDate(vs);
                }
                else if ((parsedinput[parsedinput.Length - 1] == "BC") || (parsedinput[parsedinput.Length - 1] == "B.C."))
                {
                    //BC Year
                    //DATE ABT 47000 B.C.
                    //modifier = parsedinput[0];
                    long year2;
                    try
                    {
                        year2 = long.Parse(parsedinput[1]);
                    }
                    catch (FormatException)
                    {
                        year2 = BCParse(parsedinput);
                    }
                    StarDate sd = c.netstart - year2 * c.Year;
                    sd.metadata = StarData.Local;
                    return sd;
                    throw new NotImplementedException();
                }
                else if (modifier == "BET")
                {
                    try
                    {
                        StarDate dt1 = StarDate.GregParse(parsedinput[1] + " " + parsedinput[2] + " " + parsedinput[3]);
                        StarDate dt2 = StarDate.GregParse(parsedinput[5] + " " + parsedinput[6] + " " + parsedinput[7]);
                        return between(dt1, dt2);
                    }
                    catch (IndexOutOfRangeException)
                    {
                        return between(StarDate.FromGreg(int.Parse(parsedinput[1])), StarDate.FromGreg(int.Parse(parsedinput[3])));
                    }
                }
                else if (modifier == "ABT")
                {
                    int l = int.Parse(parsedinput[1]);
                    return StarDate.FromGreg(l);
                }
                else
                {
                    string new_input = "";
                    int i = 1;
                    while (i < parsedinput.Length)
                    {
                        new_input = new_input + " " + parsedinput[i];
                        i++;
                    }
                    try
                    {
                        dt = DateTime.Parse(new_input);
                    }
                    catch (FormatException)
                    {
                        try
                        {
                            dt = DateTime.Parse(parsedinput[1] + " " + parsedinput[2] + " " + parsedinput[3]);
                        }
                        catch (IndexOutOfRangeException)
                        {
                            try
                            {
                                int year = int.Parse(input);
                                return StarDate.FromGreg(year);
                            }
                            catch (FormatException)
                            {
                                try
                                {
                                    string[] decomma = input.Split(',');
                                    string v = "";
                                    int j = 0;
                                    while (j < decomma.Length)
                                    {
                                        v = v + decomma[j++];
                                    }
                                    Console.WriteLine(v);
                                    int year = int.Parse(v);
                                    return StarDate.FromGreg(year);
                                }
                                catch (FormatException)
                                {
                                    Console.WriteLine(input);
                                    if ((parsedinput[1] == "AND"))
                                    {
                                        StarDate a = StarDate.FromGreg(int.Parse(parsedinput[0]));
                                        StarDate b = StarDate.FromGreg(int.Parse(parsedinput[2]));
                                        return between(a, b);
                                    }
                                    throw new InvalidOperationException();
                                    throw new NotImplementedException();
                                    //return c.manu;
                                }
                            }

                        }
                    }
                    //throw new NotImplementedException();
                    StarDate date = new StarDate(dt);
                    date.addModifier(modifier);
                    return date;
                }
            }
        }



        private static long BCParse(string[] parsedinput)
        {
            int i = 0;
            while (i < parsedinput.Length)
            {
                Console.WriteLine(i + " " + parsedinput[i++]);
            }
            return long.Parse(parsedinput[0]);
            throw new NotImplementedException();
        }

        private static StarDate FromGreg(int year)
        {
            StarDate dt1 = StarDate.FromGreg(year, 01, 01);
            StarDate dt2 = StarDate.FromGreg(year, 12, 31);
            return StarDate.between(dt1, dt2);
        }

        private static StarDate between(StarDate dt1, StarDate dt2)
        {
            TimeSpanInfo error = (dt1 - dt2) / 2;
            TimeSpanInfo time = (dt1.atomic + dt2.atomic) / 2;
            StarDate dt = new StarDate(time);
            dt.adderror(error);
            return dt;
        }

        private void adderror(TimeSpanInfo error)
        {
            this.error = error;
        }

        private void addModifier(string modifier)
        {
            this.Note = modifier;
        }

        internal DateTime Convert()
        {
            return new DateTime((long)(this - c.netstart).ticks);
        }

        public static StarDate operator -(StarDate d, TimeSpanInfo t)
        {
            StarDate dt = d;
            dt.atomic -= t;
            return dt;
        }

        public static TimeSpanInfo operator -(StarDate d1, StarDate d2)
        {
            return d1.atomic - d2.atomic;
        }

        public static TimeSpanInfo operator -(DateTime d1, StarDate d2)
        {
            return new StarDate(d1) - d2;
        }

        public static TimeSpanInfo operator -(StarDate d1, DateTime d2)
        {
            return d1 - new StarDate(d2);
        }

        public static bool operator ==(StarDate dt1, StarDate dt2)
        {
            if (dt1.atomic == dt2.atomic)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static bool operator !=(StarDate dt1, StarDate dt2)
        {
            throw new NotImplementedException();
        }

        public static bool operator <(StarDate dt1, StarDate dt2)
        {
            return dt1.atomic < dt2.atomic;
        }

        public static bool operator >(StarDate dt1, StarDate dt2)
        {
            return dt1.atomic > dt2.atomic;
        }

        public static bool operator <=(StarDate dt1, StarDate dt2)
        {
            if (dt1 < dt2)
            {
                return true;
            }
            else if (dt1 == dt2)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static bool operator >=(StarDate dt1, StarDate dt2)
        {
            if (dt1 > dt2)
            {
                return true;
            }
            else if (dt1 == dt2)
            {
                return true;
            }
            else
            {
                return false;
            }
        }


        public override string ToString()
        {
            return this.ToString(d.getlocale(), d.defaultformat());
        }

        public string ToString(CultureInfo local)
        {
            return this.ToString(local, d.defaultformat());
        }

        public string ToString(string format, string lang)
        {
            return this.ToString(CultureInfo.GetLocale(lang), format);
        }

        public string ToString(string format)
        {
            return this.ToString(d.getlocale(), format);
        }

        public string ToString(CultureInfo local, string format)
        {
            return local.StarDateString(this.LocalData(), format);
        }

        //private bool IsHoliday()
        //{
        //    return this.GetHoliday() != null;
        //}

        //private int billion()
        //{
        //    return this.LocalData()["b"];
        //}

        public string time()
        {
            var data = this.LocalData();
            return addzero(data["hour"]) + ":" + addzero(data["min"]) + ":" + addzero(data["second"]) + ":" + addzero(data["Milliseconds"]) + ":" + addzero(data["ticks"]);
        }

        private string addzero(long v)
        {
            if (v < 10)
            {
                return "0" + v;
            }
            else
            {
                return "" + v;
            }
        }



        //public int Month()
        //{
        //    return this.LocalData()["Month"];
        //}

        //public int day()
        //{
        //    return this.LocalData()["day"];
        //}

        //public string monthname()
        //{
        //    return monthname(d.getlocale());
        //}

        //public string monthname(CultureInfo format)
        //{
        //    return format.Month(this.Month());
        //}

        //public string DayOfWeek()
        //{
        //    return this.DayOfWeek(d.getlocale());
        //}

        //public string DayOfWeek(CultureInfo format)
        //{
        //    return format.weekday(StarDate.DayFromMonth(this.day()));
        //}
        private Dictionary<string, int> LocalData()
        {
            return LocalData("Full");
        }

        private Dictionary<string, int> LocalData(string length)
        {
            StarDate adjusted = this.Localize();
            return adjusted.Data(length);
        }

        private StarDate Localize()
        {
            if (!this.IsTerran)
            {
                return this;
            }
            else if (this.ComplexTimeZone)
            {
                return this + this.GetOffset();
            }
            else if (this.HasTimeZone)
            {
                return this + this.TimeZone.Offset(this.Convert());
            }
            else
            {
                return this;
            }
        }

        private TimeSpanInfo GetOffset()
        {
            throw new NotImplementedException();
        }

        private Dictionary<string, int> Data()
        {
            return Data("Full");
        }

        private Dictionary<string, int> Data(string length)
        {
            TimeSpanInfo LocalDay = this.TimeZone.LocalDay();
            Dictionary<string, int> dict = new Dictionary<string, int>();
            TimeSpanInfo rem = this.atomic;
            dict.Add("b", rem / c.b);
            rem %= c.b;
            dict.Add("m", rem / c.m);
            rem %= c.m;
            dict.Add("cycle_78", rem / c.Seventy_Eight);
            rem %= c.Seventy_Eight;
            if (rem / c.Sixyear >= 13)
            {
                dict.Add("cycle6", 12);
                dict.Add("cycleyears", 5);
                rem %= c.Year;
                dict.Add("Month", 13);
                //dict.Add("Month", rem / c.Month);
                rem %= c.month;
                dict.Add("day", rem / c.Day);
                dict["day"]++;
                dict["Month"]++;
                dict.Add("week of year", 52 + dict["day"] / 7);
                dict.Add("day of year", 364 + dict["day"]);
                switch (dict["day"])
                {
                    case 15:
                        Console.WriteLine("ERROR CAUGHT");
                        Console.WriteLine(dict["Month"]);
                        throw new NotImplementedException();
                    default:
                        break;
                }
            }
            else
            {
                dict.Add("cycle6", rem / c.Sixyear);
                rem %= c.Sixyear;
                dict.Add("leap", rem / (6 * c.Year));
                if (dict["leap"] == 1)
                {
                    dict.Add("cycleyears", 5);
                    rem %= c.Year;
                    dict.Add("Month", 13);
                    rem %= c.month;
                    dict.Add("day", rem / c.Day);
                    dict["Month"]++;
                    dict["day"]++;
                    dict.Add("week of year", 52 + dict["day"] / 7);
                    dict.Add("day of year", 364 + dict["day"]);
                }
                else
                {
                    dict.Add("cycleyears", rem / c.Year);
                    rem %= c.Year;
                    dict.Add("Month", rem / c.month);
                    dict.Add("week of year", rem / c.week);
                    dict.Add("day of year", rem / c.Day);
                    rem %= c.month;
                    dict.Add("day", rem / c.Day);
                    dict["Month"]++;
                    dict["day"]++;
                    dict["day of year"]++;
                    //Console.WriteLine("normal year");
                    //throw new NotImplementedException();
                }
            }

            int year = dict["cycleyears"];
            year += dict["cycle6"] * 6;
            year += dict["cycle_78"] * 78;
            dict.Add("year", year);
            if ((length == "year") || (length == "Month") || (length == "day"))
            {
                return dict;
            }

            if (this.Sol() == false)
            {
                //Console.WriteLine(this.timeZone.Names());
                throw new NotImplementedException();
            }
            rem %= c.Day;
            TimeSpanInfo rem2 = rem;


            dict.Add("hour", rem / c.Hour);
            rem %= c.Hour;
            dict.Add("min", rem / c.Minute);
            rem %= c.Minute;
            dict.Add("second", rem / c.Second);
            rem %= c.Second;
            dict.Add("Milliseconds", rem / c.Millisecond);
            rem %= c.Millisecond;
            dict.Add("ticks", (int)rem.ticks);
            year += 14 * (int)Math.Pow(10, 9);
            dict.Add("big year", year);
            dict.Add("Metric", rem2 / c.Nanodi);
            rem2 %= c.Nanodi;
            int nanoticks = (int)c.Nanodi.ticks;
            dict.Add("nanodi ticks", nanoticks);
            double nanoditick = 1 / (double)nanoticks;
            double metric = (double)rem2.ticks;
            double subnano = metric / nanoticks;
            double nano2 = subnano * Math.Pow(10, 9);
            int subnano_long = (int)Math.Round(nano2);
            dict.Add("Subnano", subnano_long);
            return dict;
        }

        internal StarData GetKind()
        {
            return this.metadata;
        }

        internal BigInteger GetTicks()
        {
            return this.atomic.ticks;
        }

        internal StarDate SpecifyKind(StarDate starDate, object local)
        {
            throw new NotImplementedException();
        }

        private bool Sol()
        {
            return this.TimeZone.Sol();
        }

        internal StarDate addtimezone(string prim)
        {
            Zone timezone = Zone.Parse(prim);
            return this.addtimezone(timezone);
        }

        private StarDate addtimezone(Zone timezone)
        {
            StarDate dt = this;
            dt.TimeZone = TimeZone;
            return dt;
        }

        public StarDate addtime(string prim)
        {
            TimeSpanInfo time = TimeSpanInfo.Parse(prim);
            return addtime(time);
        }

        private StarDate addtime(TimeSpanInfo time)
        {
            return this + time;
        }

        internal static string textform(long input)
        {
            string suffix;
            long end = input % 100;
            long ten = 10;
            if ((end / ten) == 1)
            {
                suffix = "th";
            }
            else
            {
                end %= 10;
                switch (end)
                {
                    case 1:
                        suffix = "st";
                        break;
                    case 2:
                        suffix = "nd";
                        break;
                    case 3:
                        suffix = "rd";
                        break;
                    default:
                        suffix = "th";
                        break;
                }
            }

            return (input + suffix);
        }

        internal static string textform(int input)
        {
            string suffix;
            int end = input % 100;
            int ten = 10;
            if ((end / ten) == 1)
            {
                suffix = "th";
            }
            else
            {
                end %= 10;
                switch (end)
                {
                    case 1:
                        suffix = "st";
                        break;
                    case 2:
                        suffix = "nd";
                        break;
                    case 3:
                        suffix = "rd";
                        break;
                    default:
                        suffix = "th";
                        break;
                }
            }

            return (input + suffix);

            //MannicDay[] YearArray = MannicYear(year, 1);

        }

        public bool isleapyear()
        {
            throw new NotImplementedException();
        }

        public int getyear()
        {
            throw new NotImplementedException();
        }

        public static int isleapyear(long year)
        {
            if (year % 76 == 0)
            {
                return 2;
            }
            else if (year % 6 == 0)
            {
                return 1;
            }
            else
            {
                return 0;
            }
        }

        public static bool leapbool(long year)
        {
            return year % 6 == 0;
        }

        public override bool Equals(object obj)
        {
            throw new NotImplementedException();
        }

        public override int GetHashCode()
        {
            throw new NotImplementedException();
        }

        internal static void Test()
        {
            StarDate dt = StarDate.Now;
            //Console.WriteLine(dt);
            bool gab = true;
            while (gab)
            {
                Console.WriteLine(dt);
                dt += c.Day;
            }
        }

        public static StarDate FromGreg(int year, int month, int day)
        {
            int hour = 0;
            int min = 0;
            int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour)
        {
            //int hour = 0;
            int min = 0;
            int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min)
        {
            //int hour = 0;
            //int min = 0;
            int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min, int sec)
        {
            //int hour = 0;
            //int min = 0;
            //int sec = 0;
            int mil = 0;
            return FromGreg(year, month, day, hour, min, sec, mil);
        }

        public static StarDate FromGreg(int year, int month, int day, int hour, int min, int sec, int mil)
        {
            try
            {
                return new StarDate(new DateTime(year, month, day, hour, min, sec, mil));
            }
            catch (System.ArgumentOutOfRangeException)
            {
                return MathFromGreg(year, month, day, hour, min, sec, mil);
            }
        }

        public static StarDate MathFromGreg(int year, int month, int day, int hour, int min, int sec, int mil)
        {
            //Console.WriteLine(year + " " + Month + " " + day + " " + hour + " " + sec + " " + mil);
            // Number of days in a non-leap year
            int DaysPerYear = 365;
            // Number of days in 4 years
            int DaysPer4Years = DaysPerYear * 4 + 1;       // 1461
                                                           // Number of days in 100 years
            int DaysPer100Years = DaysPer4Years * 25 - 1;  // 36524
                                                           // Number of days in 400 years
            int DaysPer400Years = DaysPer100Years * 4 + 1; // 146097
            int[] DaysToMonth365 = {
                    0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
            int[] DaysToMonth366 = {
                    0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};
            bool leapyear = GregLeap(year);
            int[] timespans = GregSpans(year);
            StarDate output = new StarDate(c.netstart.atomic);
            output += timespans[0] * DaysPer400Years * c.Day;
            output += timespans[1] * DaysPer100Years * c.Day;
            output += timespans[2] * DaysPer4Years * c.Day;
            output += timespans[3] * DaysPerYear * c.Day;
            int days;
            if (leapyear)
            {
                try
                {
                    days = DaysToMonth366[month - 1];
                }
                catch (IndexOutOfRangeException)
                {
                    Console.WriteLine(month - 1);
                    throw new NotImplementedException();
                }
            }
            else
            {
                days = DaysToMonth365[month - 1];
            }
            days += day - 1;
            //Console.WriteLine(days);
            output += days * c.Day;
            output += hour * c.Hour;
            output += min * c.Minute;
            output += sec * c.Second;
            output += mil * c.Millisecond;
            return output;
            //throw new NotImplementedException();
        }

        public static bool GregLeap(int year)
        {
            if (year < 1)
            {
                year++;
            }

            if (year % 400 == 0)
            {
                return true;
            }
            else if (year % 100 == 0)
            {
                return false;
            }
            else if (year % 4 == 0)
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static void testtimespans()
        {
            int i = 401;
            while (i > -415)
            {
                int[] r = StarDate.GregSpans(i--);
                if (i == 0)
                {
                    i--;
                }
            }
        }

        internal static int[] GregSpans(int year)
        {
            if (year < 1)
            {
                year++;
            }
            year--;
            int yearmod = year % 400;
            if (yearmod < 0)
            {
                yearmod += 400;
            }
            int quattro = (year - yearmod) / 400;
            //Console.WriteLine" 400mod = " + yearmod);
            //Console.WriteLine" 400count = " + quattro);
            int centcount = yearmod / 100;
            yearmod %= 100;
            //Console.WriteLine" centcount = " + centcount);
            int leapcount = yearmod / 4;
            yearmod %= 4;
            int yearcount = yearmod;
            //Console.WriteLine" q " + quattro + " c +" + centcount + " l +" + leapcount + " y +" + yearcount);
            //Console.WriteLine(" ");
            return new int[] { quattro, centcount, leapcount, yearcount };
        }

        public string MathGregString()
        {
            int[] r = this.MathGregNumbers();
            return r[0] + "-" + r[1] + "-" + r[2];
        }

        public string GregString()
        {
            int[] r = this.GregNumbers();
            return r[0] + "-" + r[1] + "-" + r[2];
        }

        public int[] GregNumbers()
        {
            try
            {
                DateTime dt = this.Convert();
                return new int[] { dt.Year, dt.Month, dt.Day };
            }
            catch (ArgumentOutOfRangeException)
            {

            }
            catch (OverflowException)
            {

            }
            return MathGregNumbers();
        }

        internal void GetDatePart(out int year, out int month, out int day)
        {
            throw new NotImplementedException();
        }

        public int[] MathGregNumbers()
        {
            {
                int DaysPerYear = 365;
                // Number of days in 4 years
                int DaysPer4Years = DaysPerYear * 4 + 1;       // 1461
                                                               // Number of days in 100 years
                int DaysPer100Years = DaysPer4Years * 25 - 1;  // 36524
                                                               // Number of days in 400 years
                int DaysPer400Years = DaysPer100Years * 4 + 1; // 146097
                                                               //TimeSpanInfo q = DaysPer400Years * c.Day;
                                                               //TimeSpanInfo s = DaysPer100Years * c.Day;
                                                               //TimeSpanInfo l = DaysPer4Years * c.Day;
                                                               //TimeSpanInfo y = DaysPerYear * c.Day;
                int[] DaysToMonth365 = {
                    0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
                int[] DaysToMonth366 = {
                    0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};
                if (this == c.netstart)
                {
                    return new int[] { 1, 1, 1 };
                }
                else if (this < c.netstart)
                {
                    TimeSpanInfo t = this - c.netstart;


                    //Console.WriteLine("testing");

                    //Console.WriteLine(t);

                    int days = t / c.Day;
                    //Console.WriteLine("days from netstart = " + days);

                    int q = days / DaysPer400Years;
                    int qmod = days % DaysPer400Years;
                    //Console.WriteLine(q);
                    //Console.WriteLine(qmod);
                    if (qmod < 0)
                    {
                        qmod = DaysPer400Years + qmod;
                        q--;
                    }
                    //Console.WriteLine(q);
                    //Console.WriteLine(qmod);
                    int s = qmod / DaysPer100Years;
                    int smod = qmod % DaysPer100Years;
                    int l = smod / DaysPer4Years;
                    int lmod = smod % DaysPer4Years;
                    int y = lmod / DaysPerYear;
                    int ymod = lmod % DaysPerYear;
                    //Console.WriteLine(s);
                    //Console.WriteLine(l);
                    //Console.WriteLine(y);
                    int m = 500;
                    int yd = ymod;
                    int d = 500;
                    int year = 400 * q + 100 * s + 4 * l + y;
                    //if (year < 1)
                    //{
                    //    year--;
                    //}
                    if (s == 4)
                    {
                        s = 3;
                        l = 24;
                        y = 3;
                        m = 11;
                        d = 31;
                        year--;
                    }
                    else if (GregLeap(year) == true)
                    {
                        int i = 0;
                        bool found = false;
                        while (!found)
                        {
                            //Console.WriteLine(DaysToMonth366[i]);
                            if (DaysToMonth366[i] > yd)
                            {
                                m = i - 1;
                                found = true;
                                //Console.WriteLine("366");
                                d = yd - DaysToMonth366[m] + 1;
                            }
                            else
                            {
                                i++;
                            }
                        }
                    }
                    else
                    {
                        //Console.WriteLine(GregLeap(year));
                        int i = 0;
                        bool found = false;
                        while (!found)
                        {
                            //Console.WriteLine(DaysToMonth366[i]);
                            if (DaysToMonth365[i] > yd)
                            {
                                m = i - 1;
                                found = true;
                                d = yd - DaysToMonth365[m] + 1;
                            }
                            else
                            {
                                i++;
                            }
                        }
                    }
                    //Console.WriteLine(year + " " + m + " " + d + " ");
                    //throw new NotImplementedException();
                    if (d == 0)
                    {
                        throw new NotImplementedException();
                    }
                    m++;
                    if (this > c.netstart)
                    {
                        //Console.WriteLine("TEST");
                        year++;
                    }
                    return new int[] { year, m, d };
                }
                else // this > c.netstart
                {
                    int year;
                    int t = (this - c.netstart) / c.Day;
                    int q = t / DaysPer400Years;
                    t %= DaysPer400Years;
                    int s = t / DaysPer100Years;
                    if (s == 4)
                    {
                        year = 1 + 400 * q + 399;
                        return new int[] { year, 12, 31 };
                        throw new NotImplementedException();
                    }
                    t %= DaysPer100Years;
                    int l = t / DaysPer4Years;
                    t %= DaysPer4Years;
                    int y = t / DaysPerYear;
                    var months = DaysToMonth365;
                    year = 1 + 400 * q + 100 * s + 4 * l + y;
                    if (GregLeap(year))
                    {
                        months = DaysToMonth366;
                    }
                    t %= DaysPerYear;


                    int m = 500;
                    int d = 500;

                    int i = 0;
                    bool found = false;
                    while (!found)
                    {
                        //Console.WriteLine(DaysToMonth366[i]);
                        if (months[i] > t)
                        {
                            m = i - 1;
                            found = true;
                            //Console.WriteLine("366");
                            d = t - months[m] + 1;
                        }
                        else
                        {
                            i++;
                        }
                    }

                    return new int[] { year, m + 1, d };
                }
            }
        }

        internal StarDate ToUniversalTime()
        {
            throw new NotImplementedException();
        }

        internal int DayOfWeekInt()
        {
            throw new NotImplementedException();
        }

        internal static DateTime GregChineseNewYear(DateTime now)
        {
            Calendar Chinese = new ChineseLunisolarCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 4, 1);
            int ChinaYear = Chinese.GetYear(now);
            DateTime Hanukkah = new DateTime(ChinaYear, 1, 1, new ChineseLunisolarCalendar());
            return Hanukkah;
        }

        internal static DateTime GregChineseNewYear()
        {
            return GregChineseNewYear(DateTime.Now);
        }


        public static StarDate StarPurim()
        {
            return new StarDate(GregPurim());
        }

        public static StarDate StarPurim(DateTime dt)
        {
            return new StarDate(GregPurim(dt));
        }

        public static StarDate StarPurim(StarDate dt)
        {
            return new StarDate(GregPurim(dt));
        }

        public static DateTime GregPurim()
        {
            return GregPurim(DateTime.Now);
        }

        public static DateTime GregPurim(DateTime now)
        {
            Calendar HebCal = new HebrewCalendar();
            int i = now.Year;
            DateTime h = new DateTime(i, 11, 1);
            int hebyear = HebCal.GetYear(now);
            DateTime Purim = new DateTime(hebyear, 6, 14, new HebrewCalendar());
            return Purim;
        }

        public static DateTime GregPurim(StarDate dt)
        {
            DateTime o = new StarDate(dt.year, 12, 1).Convert();
            return GregPurim(o);
        }

        public static implicit operator DateTime(StarDate dt)
        {
            return dt.Convert();
        }

        public StarDate addYears(long years)
        {
            throw new NotImplementedException();
        }

        public StarDate addMonths(long years)
        {
            throw new NotImplementedException();
        }

        public StarDate addWeeks(long years)
        {
            throw new NotImplementedException();
        }

        public StarDate addDays(long years)
        {
            throw new NotImplementedException();
        }

        public StarDate addHours(long years)
        {
            throw new NotImplementedException();
        }

        public StarDate addMinutes(long min)
        {
            throw new NotImplementedException();
        }

        public StarDate addSeconds(long seconds)
        {
            throw new NotImplementedException();
        }

        public StarDate addMilliseconds(long years)
        {
            throw new NotImplementedException();
        }

        public StarDate addTicks(long years)
        {
            throw new NotImplementedException();
        }
    }
}