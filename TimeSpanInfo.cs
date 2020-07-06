using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;

namespace StarCalendar
{
    public struct TimeSpanInfo : IComparable<TimeSpanInfo>, IEquatable<TimeSpanInfo>
    {
        internal BigInteger ticks;
        internal static TimeSpanInfo Zero;
        //private int milliseconds;
        //private int seconds;
        //private int days;

        //public static TimeSpanInfo MinValue { get; internal set; }
        public static int TicksPerSecond = (int) c.Second.ticks;
        public int Hours
        {
            get { return this / c.Hour; }
            //internal set
            //{
            //    throw new NotImplementedException();
            //    //hours = value;
            //}
        }
        public int Minutes
        {
            get { return this / c.Minute; }
            //internal set
            //{
            //    throw new NotImplementedException();
            //    //minutes = value;
            //}
        }

        public int Days
        {
            get
            {
                return this / c.Day;
            }

            //internal set
            //{
            //    days = value;
            //}
        }
        public int Seconds
        {
            get
            {
                return this / c.Second;
            }

            //internal set
            //{
            //    seconds = value;
            //}
        }
        public int Milliseconds
        {
            get
            {
                return this / c.Millisecond;
            }

            //internal set
            //{
            //    milliseconds = value;
            //}
        }

        public TimeSpanInfo(long ticks)
        {
            this.ticks = ticks;
        }

        public TimeSpanInfo(BigInteger bigInteger)
        {
            this.ticks = bigInteger;
        }

        public TimeSpanInfo(TimeSpan t) : this()
        {
            this.ticks = t.Ticks;
        }

        public static explicit operator TimeSpanInfo(TimeSpan v)
        {
            return new TimeSpanInfo(v);
        }

        public static TimeSpanInfo operator +(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return new TimeSpanInfo(t1.ticks + t2.ticks);
        }

        public static TimeSpanInfo operator -(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return new TimeSpanInfo(t1.ticks - t2.ticks);
        }

        public static TimeSpanInfo operator *(long l, TimeSpanInfo t)
        {
            return t * l;
        }

        public static TimeSpanInfo operator *(TimeSpanInfo t, long l)
        {
            return new TimeSpanInfo(t.ticks * l);
        }

        public static int operator /(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            int d = 0;
            BigInteger big = t1.ticks / t2.ticks;
            d += (int)big;
            return d;

        }

        public static TimeSpanInfo operator /(TimeSpanInfo t, BigInteger i)
        {
            return new TimeSpanInfo(t.ticks / i);
        }

        public static TimeSpanInfo operator *(TimeSpanInfo t, double d)
        {
            return d * t;
        }

        public static TimeSpanInfo operator *(double d, TimeSpanInfo t)
        {
            TimeSpanInfo newtime = t * (int)d;
            string[] vs = d.ToString(NumberFormatInfo.InvariantInfo).Split('.');
            string s = "00";
            try
            {
                s = vs[1];
            }
            catch (IndexOutOfRangeException)
            {

            }
            int decimalcount = s.Length;
            int i = 0;
            //BigInteger[] decimals = new BigInteger[decimalcount];
            while (i < decimalcount)
            {
                int mult = (int)char.GetNumericValue(s[i]);
                int dec = (int)Math.Pow(10, i + 1);
                BigInteger big = (t.ticks / dec) * mult;
                newtime.ticks += big;
                //decimals[i] = big;
                i++;
            }
            return newtime;
        }

        public static explicit operator TimeSpan(TimeSpanInfo v)
        {
            throw new NotImplementedException();
        }

        public static TimeSpanInfo operator %(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return new TimeSpanInfo(t1.ticks % t2.ticks);
        }

        bool IEquatable<TimeSpanInfo>.Equals(TimeSpanInfo other)
        {
            throw new NotImplementedException();
        }

        public bool Equals(TimeSpanInfo other)
        {
            return this.ticks == other.ticks;
        }

        int IComparable<TimeSpanInfo>.CompareTo(TimeSpanInfo other)
        {
            return (this.ticks - other.ticks).Sign;
        }

        public TimeSpan TimeSpan => new TimeSpan((long)this.ticks);

        public static bool operator ==(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return t1.Equals(t2);
        }

        public static bool operator !=(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return !(t1.Equals(t2));
        }

        public static bool operator ==(TimeSpan timeSpan, TimeSpanInfo timeSpanInfo)
        {
            return timeSpanInfo == timeSpan;
        }

        public static bool operator ==(TimeSpanInfo timeSpanInfo, TimeSpan timeSpan)
        {
            return timeSpanInfo.ticks == timeSpan.Ticks;
        }

        public static bool operator !=(TimeSpan timeSpan, TimeSpanInfo timeSpanInfo)
        {
            return timeSpanInfo != timeSpan;
        }

        public static bool operator !=(TimeSpanInfo timeSpanInfo, TimeSpan timeSpan)
        {
            return timeSpanInfo.ticks != timeSpan.Ticks;
        }

        public static bool operator <(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return t1.ticks < t2.ticks;
        }

        public static bool operator >(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return t1.ticks > t2.ticks;
        }

        public static bool operator >=(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return (t1 == t2) || (t1 > t2);
        }

        public static bool operator <=(TimeSpanInfo t1, TimeSpanInfo t2)
        {
            return (t1 == t2) || (t1 < t2);
        }

        //internal Dictionary<string, double> timespandata(TimeSpanInfo day)
        //{
        //    Dictionary<string, double> data = new Dictionary<string, double>();
        //    data["years"] = this / c.Year;
        //    TimeSpanInfo rem = this % c.Year;
        //    data["months"] = rem / day;
        //    data["weeks"] = rem / c.week;
        //    throw new NotImplementedException();
        //    rem %= c.Day;

        //    data["day"] = rem / day;
        //    rem %= day;
        //    TimeSpanInfo daytime = rem;
        //    data["hour"] = rem / c.Hour;
        //    rem %= c.Hour;
        //    data["minute"] = rem / c.Minute;
        //    rem %= c.Minute;
        //    data["second"] = rem / c.Second;
        //    rem %= c.Second;
        //    data["millisec"] = rem / c.Millisecond;
        //    rem %= c.Millisecond;
        //    data["ticks"] = (int)rem.ticks;
        //    rem = daytime;
        //    data["Centidi"] = rem / c.Centidi;
        //    rem %= c.Centidi;
        //    data["Millidi"] = rem / c.Millidi;
        //    rem %= c.Millidi;
        //    data["Microdi"] = rem / c.Microdi;
        //    rem %= c.Microdi;
        //    data["Nanodi"] = rem / c.Nanodi;
        //    rem %= c.Nanodi;
        //    data["Nanodi Ticks"] = (int)rem.ticks;
        //    return data;
        //}

        public override string ToString()
        {
            return this.data("year") + "-" + this.data("Month") + "-" + this.data("day");
        }

        private int data(string v)
        {
            return this.data()[v];
        }

        private Dictionary<string, int> data()
        {
            TimeSpanInfo t = this;
            Dictionary<string, int> k = new Dictionary<string, int>();
            k.Add("year", t / c.Year);
            t %= c.Year;
            k.Add("Month", t / c.month);
            t %= c.month;
            k.Add("day", t / c.Day);
            t %= c.Day;
            return k;
        }

        internal static TimeSpanInfo Parse(string prim)
        {
            TimeSpan time = TimeSpan.Parse(prim);
            return new TimeSpanInfo(time);
        }

        public override bool Equals(object obj)
        {
            throw new NotImplementedException();
        }

        public override int GetHashCode()
        {
            throw new NotImplementedException();
        }

        //public int days()
        //{
        //    return this / c.Day;
        //}

        internal TimeSpanInfo Negate()
        {
            throw new NotImplementedException();
        }
    }
}