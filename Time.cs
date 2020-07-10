using System.Text;
using System;
using System.Runtime;
using System.Runtime.CompilerServices;
using System.Runtime.Versioning;
using System.Diagnostics.Contracts;
using System.Globalization;
using System.Numerics;
using System.Collections.Generic;

namespace StarCalendar
{
    

    // Time represents a duration of time.  A Time can be negative
    // or positive.
    //
    // Time is internally represented as a number of milliseconds.  While
    // this maps well into units of time such as hours and days, any
    // periods longer than that aren't representable in a nice fashion.
    // For instance, a month can be between 28 and 31 days, while a Year
    // can contain 365 or 364 days.  A decade can have between 1 and 3 leapyears,
    // depending on when you map the Time into the calendar.  This is why
    // we do not provide Years() or Months().
    //
    // Note: System.Time needs to interop with the WinRT structure
    // type Windows::Foundation:Time. These types are currently binary-compatible in
    // memory so no custom marshalling is required. If at any point the implementation
    // details of this type should change, or new fields added, we need to remember to add
    // an appropriate custom ILMarshaler to keep WInRT interop scenarios enabled.
    //
    [System.Runtime.InteropServices.ComVisible(true)]
    [Serializable]
    public struct Time : IComparable, IComparable<Time>, IEquatable<Time>, IFormattable
//#if GENERICS_WORK
//        , IComparable<Time>, IEquatable<Time>, IFormattable
//#endif
    {
        public const long TicksPerMillisecond = 10000;
        private const double MillisecondsPerTick = 1.0 / TicksPerMillisecond;

        public const long TicksPerSecond = TicksPerMillisecond * 1000;   // 10,000,000
        private const double SecondsPerTick = 1.0 / TicksPerSecond;         // 0.0001

        public const long TicksPerMinute = TicksPerSecond * 60;         // 600,000,000
        private const double MinutesPerTick = 1.0 / TicksPerMinute; // 1.6666666666667e-9

        public const long TicksPerHour = TicksPerMinute * 60;        // 36,000,000,000
        private const double HoursPerTick = 1.0 / TicksPerHour; // 2.77777777777777778e-11

        public const long TicksPerDay = TicksPerHour * 24;          // 864,000,000,000
        private const double DaysPerTick = 1.0 / TicksPerDay; // 1.1574074074074074074e-12

        private const int MillisPerSecond = 1000;
        private const int MillisPerMinute = MillisPerSecond * 60; //     60,000
        private const int MillisPerHour = MillisPerMinute * 60;   //  3,600,000
        private const int MillisPerDay = MillisPerHour * 24;      // 86,400,000

        internal const long MaxSeconds = Int64.MaxValue / TicksPerSecond;
        internal const long MinSeconds = Int64.MinValue / TicksPerSecond;

        internal const long MaxMilliSeconds = Int64.MaxValue / TicksPerMillisecond;
        internal const long MinMilliSeconds = Int64.MinValue / TicksPerMillisecond;

        internal const long TicksPerTenthSecond = TicksPerMillisecond * 100;

        public static readonly Time Zero = new Time(0);

        public static readonly Time MaxValue = new Time(Int64.MaxValue);
        public static readonly Time MinValue = new Time(Int64.MinValue);

        // internal so that DateTime doesn't have to call an extra get
        // method for some arithmetic operations.
        //internal BigInteger _ticks;

        //public Time() {
        //    _ticks = 0;
        //}

        public Time(long ticks)
        {
            this._ticks = ticks;
        }

        public Time(int hours, int minutes, int seconds)
        {
            _ticks = TimeToTicks(hours, minutes, seconds);
        }

        public Time(int days, int hours, int minutes, int seconds)
            : this(days, hours, minutes, seconds, 0)
        {
        }

        public Time(int days, int hours, int minutes, int seconds, int milliseconds)
        {
            Int64 totalMilliSeconds = ((Int64)days * 3600 * 24 + (Int64)hours * 3600 + (Int64)minutes * 60 + seconds) * 1000 + milliseconds;
            if (totalMilliSeconds > MaxMilliSeconds || totalMilliSeconds < MinMilliSeconds)
                throw new ArgumentOutOfRangeException(); //Environment.GetResourceString("Overflow_TimeTooLong"));
            _ticks = (long)totalMilliSeconds * TicksPerMillisecond;
        }

        public BigInteger Ticks
        {
            get { return _ticks; }
        }

        public int Days
        {
            get { return (int)(_ticks / TicksPerDay); }
        }

        public int Hours
        {
            get { return (int)((_ticks / TicksPerHour) % 24); }
        }

        public int Milliseconds
        {
            get { return (int)((_ticks / TicksPerMillisecond) % 1000); }
        }

        public int Minutes
        {
            get { return (int)((_ticks / TicksPerMinute) % 60); }
        }

        public int Seconds
        {
            get { return (int)((_ticks / TicksPerSecond) % 60); }
        }

        public double TotalDays
        {
            get { return ((double)_ticks) * DaysPerTick; }
        }

        public double TotalHours
        {
            get { return (double)_ticks * HoursPerTick; }
        }

        public double TotalMilliseconds
        {
            get
            {
                double temp = (double)_ticks * MillisecondsPerTick;
                if (temp > MaxMilliSeconds)
                    return (double)MaxMilliSeconds;

                if (temp < MinMilliSeconds)
                    return (double)MinMilliSeconds;

                return temp;
            }
        }

        public double TotalMinutes
        {
            get { return (double)_ticks * MinutesPerTick; }
        }

        public double TotalSeconds
        {
            get { return (double)_ticks * SecondsPerTick; }
        }

        public Time Add(Time ts)
        {
            BigInteger result = _ticks + ts._ticks;
            // Overflow if signs of operands was identical and result's
            // sign was opposite.
            // >> 63 gives the sign bit (either 64 1's or 64 0's).
            if ((_ticks >> 63 == ts._ticks >> 63) && (_ticks >> 63 != result >> 63))
                throw new OverflowException(); //Environment.GetResourceString("Overflow_TimeTooLong"));
            return new Time(result);
        }


        // Compares two Time values, returning an integer that indicates their
        // relationship.
        //
        public static int Compare(Time t1, Time t2)
        {
            if (t1._ticks > t2._ticks) return 1;
            if (t1._ticks < t2._ticks) return -1;
            return 0;
        }

        // Returns a value less than zero if this  object
        public int CompareTo(Object value)
        {
            if (value == null) return 1;
            if (!(value is Time))
                throw new ArgumentException(); //Environment.GetResourceString("Arg_MustBeTime"));
            BigInteger t = ((Time)value)._ticks;
            if (_ticks > t) return 1;
            if (_ticks < t) return -1;
            return 0;
        }

#if GENERICS_WORK
        public int CompareTo(Time value) {
            long t = value._ticks;
            if (_ticks > t) return 1;
            if (_ticks < t) return -1;
            return 0;
        }
#endif

        public static Time FromDays(double value)
        {
            return Interval(value, MillisPerDay);
        }

        public Time Duration()
        {
            if (Ticks == Time.MinValue.Ticks)
                throw new OverflowException(); //Environment.GetResourceString("Overflow_Duration"));
            Contract.EndContractBlock();
            return new Time(_ticks >= 0 ? _ticks : -_ticks);
        }

        public override bool Equals(Object value)
        {
            if (value is Time)
            {
                return _ticks == ((Time)value)._ticks;
            }
            return false;
        }

        public bool Equals(Time obj)
        {
            return _ticks == obj._ticks;
        }

        public static bool Equals(Time t1, Time t2)
        {
            return t1._ticks == t2._ticks;
        }

        public override int GetHashCode()
        {
            return (int)_ticks ^ (int)(_ticks >> 32);
        }

        public static Time FromHours(double value)
        {
            return Interval(value, MillisPerHour);
        }

        private static Time Interval(double value, int scale)
        {
            if (Double.IsNaN(value))
                throw new ArgumentException(); //Environment.GetResourceString("Arg_CannotBeNaN"));
            Contract.EndContractBlock();
            double tmp = value * scale;
            double millis = tmp + (value >= 0 ? 0.5 : -0.5);
            if ((millis > Int64.MaxValue / TicksPerMillisecond) || (millis < Int64.MinValue / TicksPerMillisecond))
                throw new OverflowException(); //Environment.GetResourceString("Overflow_TimeTooLong"));
            return new Time((long)millis * TicksPerMillisecond);
        }

        public static Time FromMilliseconds(double value)
        {
            return Interval(value, 1);
        }

        public static Time FromMinutes(double value)
        {
            return Interval(value, MillisPerMinute);
        }

        //public Time Negate()
        //{
        //    if (Ticks == Time.MinValue.Ticks)
        //        throw new OverflowException(); //Environment.GetResourceString("Overflow_NegateTwosCompNum"));
        //    Contract.EndContractBlock();
        //    return new Time(-_ticks);
        //}

        public static Time FromSeconds(double value)
        {
            return Interval(value, MillisPerSecond);
        }

        public Time Subtract(Time ts)
        {
            BigInteger result = _ticks - ts._ticks;
            // Overflow if signs of operands was different and result's
            // sign was opposite from the first argument's sign.
            // >> 63 gives the sign bit (either 64 1's or 64 0's).
            if ((_ticks >> 63 != ts._ticks >> 63) && (_ticks >> 63 != result >> 63))
                throw new OverflowException(); //Environment.GetResourceString("Overflow_TimeTooLong"));
            return new Time(result);
        }

        public static Time FromTicks(long value)
        {
            return new Time(value);
        }

        internal static long TimeToTicks(int hour, int minute, int second)
        {
            // totalSeconds is bounded by 2^31 * 2^12 + 2^31 * 2^8 + 2^31,
            // which is less than 2^44, meaning we won't overflow totalSeconds.
            long totalSeconds = (long)hour * 3600 + (long)minute * 60 + (long)second;
            if (totalSeconds > MaxSeconds || totalSeconds < MinSeconds)
                throw new ArgumentOutOfRangeException(); //Environment.GetResourceString("Overflow_TimeTooLong"));
            return totalSeconds * TicksPerSecond;
        }

        public static Time Parse(string s)
        {
            return (Time)TimeSpan.Parse(s);
        }

        public static Time operator -(Time t)
        {
            if (t._ticks == Time.MinValue._ticks)
                throw new OverflowException(); //Environment.GetResourceString("Overflow_NegateTwosCompNum"));
            return new Time(-t._ticks);
        }

        public static Time operator -(Time t1, Time t2)
        {
            return t1.Subtract(t2);
        }

        public static Time operator +(Time t)
        {
            return t;
        }

        public static Time operator +(Time t1, Time t2)
        {
            return t1.Add(t2);
        }

        public static bool operator ==(Time t1, Time t2)
        {
            return t1._ticks == t2._ticks;
        }

        public static bool operator !=(Time t1, Time t2)
        {
            return t1._ticks != t2._ticks;
        }

        //public static bool operator <(Time t1, Time t2)
        //{
        //    return t1._ticks < t2._ticks;
        //}

        //public static bool operator <=(Time t1, Time t2)
        //{
        //    return t1._ticks <= t2._ticks;
        //}

        //public static bool operator >(Time t1, Time t2)
        //{
        //    return t1._ticks > t2._ticks;
        //}

        //public static bool operator >=(Time t1, Time t2)
        //{
        //    return t1._ticks >= t2._ticks;
        //}


        //
        // In .NET Framework v1.0 - v3.5 System.Time did not implement IFormattable
        //    The composite formatter ignores format specifiers on types that do not implement
        //    IFormattable, so the following code would 'just work' by using Time.ToString()
        //    under the hood:
        //        String.Format("{0:_someRandomFormatString_}", myTime);      
        //    
        // In .NET Framework v4.0 System.Time implements IFormattable.  This causes the 
        //    composite formatter to call Time.ToString(string format, FormatProvider provider)
        //    and pass in "_someRandomFormatString_" for the format parameter.  When the format 
        //    parameter is invalid a FormatException is thrown.
        //
        // The 'NetFx40_TimeLegacyFormatMode' per-AppDomain configuration option and the 'Time_LegacyFormatMode' 
        // process-wide configuration option allows applications to run with the v1.0 - v3.5 legacy behavior.  When
        // either switch is specified the format parameter is ignored and the default output is returned.
        //
        // There are three ways to use the process-wide configuration option:
        //
        // 1) Config file (MyApp.exe.config)
        //        <?xml version ="1.0"?>
        //        <configuration>
        //         <runtime>
        //          <Time_LegacyFormatMode enabled="true"/>
        //         </runtime>
        //        </configuration>
        // 2) Environment variable
        //        set COMPLUS_Time_LegacyFormatMode=1
        // 3) RegistryKey
        //        [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\.NETFramework]
        //        "Time_LegacyFormatMode"=dword:00000001
        //
#if !FEATURE_CORECLR
        [System.Security.SecurityCritical]
        [ResourceExposure(ResourceScope.None)]
        [MethodImplAttribute(MethodImplOptions.InternalCall)]
        private static extern bool LegacyFormatMode();

#endif // !FEATURE_CORECLR

        //private static bool LegacyMode
        //{
        //    get
        //    {
        //        if (!_legacyConfigChecked)
        //        {
        //            // no need to lock - idempotent
        //            _legacyMode = GetLegacyFormatMode();
        //            _legacyConfigChecked = true;
        //        }
        //        return _legacyMode;
        //    }
        //}

        internal BigInteger _ticks;


        public Time(BigInteger bigInteger)
        {
            this._ticks = bigInteger;
        }

        public Time(TimeSpan t) : this()
        {
            this._ticks = t.Ticks;
        }

        public static explicit operator Time(TimeSpan v)
        {
            return new Time(v);
        }

        //public static Time operator +(Time t1, Time t2)
        //{
        //    return new Time(t1._ticks + t2._ticks);
        //}

        //public static Time operator -(Time t1, Time t2)
        //{
        //    return new Time(t1._ticks - t2._ticks);
        //}

        public static Time operator *(long l, Time t)
        {
            return t * l;
        }

        public static Time operator *(Time t, long l)
        {
            return new Time(t._ticks * l);
        }

        public static int operator /(Time t1, Time t2)
        {
            int d = 0;
            BigInteger big = t1._ticks / t2._ticks;
            d += (int)big;
            return d;

        }

        public static Time operator /(Time t, BigInteger i)
        {
            return new Time(t._ticks / i);
        }

        public static Time operator *(Time t, double d)
        {
            return d * t;
        }

        public static Time operator *(double d, Time t)
        {
            Time newtime = t * (int)d;
            string[] vs = d.ToString(System.Globalization.NumberFormatInfo.InvariantInfo).Split('.');
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
                BigInteger big = (t._ticks / dec) * mult;
                newtime._ticks += big;
                //decimals[i] = big;
                i++;
            }
            return newtime;
        }

        public static explicit operator TimeSpan(Time v)
        {
            throw new NotImplementedException();
        }

        public static Time operator %(Time t1, Time t2)
        {
            return new Time(t1._ticks % t2._ticks);
        }

        bool IEquatable<Time>.Equals(Time other)
        {
            throw new NotImplementedException();
        }

        //public bool Equals(Time other)
        //{
        //    return this._ticks == other._ticks;
        //}

        int IComparable<Time>.CompareTo(Time other)
        {
            return (this._ticks - other._ticks).Sign;
        }

        public TimeSpan TimeSpan => new TimeSpan((long)this._ticks);

        //public static bool operator ==(Time t1, Time t2)
        //{
        //    return t1.Equals(t2);
        //}

        //public static bool operator !=(Time t1, Time t2)
        //{
        //    return !(t1.Equals(t2));
        //}

        public static bool operator ==(TimeSpan timeSpan, Time timeSpanInfo)
        {
            return timeSpanInfo == timeSpan;
        }

        public static bool operator ==(Time timeSpanInfo, TimeSpan timeSpan)
        {
            return timeSpanInfo._ticks == timeSpan.Ticks;
        }

        public static bool operator !=(TimeSpan timeSpan, Time timeSpanInfo)
        {
            return timeSpanInfo != timeSpan;
        }

        public static bool operator !=(Time timeSpanInfo, TimeSpan timeSpan)
        {
            return timeSpanInfo._ticks != timeSpan.Ticks;
        }

        public static bool operator <(Time t1, Time t2)
        {
            return t1._ticks < t2._ticks;
        }

        public static bool operator >(Time t1, Time t2)
        {
            return t1._ticks > t2._ticks;
        }

        public static bool operator >=(Time t1, Time t2)
        {
            return (t1 == t2) || (t1 > t2);
        }

        public static bool operator <=(Time t1, Time t2)
        {
            return (t1 == t2) || (t1 < t2);
        }

        //internal Dictionary<string, double> timespandata(Time day)
        //{
        //    Dictionary<string, double> data = new Dictionary<string, double>();
        //    data["years"] = this / StarDate.Year;
        //    Time rem = this % StarDate.Year;
        //    data["months"] = rem / day;
        //    data["weeks"] = rem / StarDate.week;
        //    throw new NotImplementedException();
        //    rem %= StarDate.DayTime;

        //    data["day"] = rem / day;
        //    rem %= day;
        //    Time daytime = rem;
        //    data["hour"] = rem / StarDate.HourTime;
        //    rem %= StarDate.HourTime;
        //    data["Minute"] = rem / StarDate.MinuteTime;
        //    rem %= StarDate.MinuteTime;
        //    data["second"] = rem / StarDate.SecondTime;
        //    rem %= StarDate.SecondTime;
        //    data["millisec"] = rem / StarDate.MillisecondTime;
        //    rem %= StarDate.MillisecondTime;
        //    data["_ticks"] = (int)rem._ticks;
        //    rem = daytime;
        //    data["Centidi"] = rem / StarDate.Centidi;
        //    rem %= StarDate.Centidi;
        //    data["Millidi"] = rem / StarDate.Millidi;
        //    rem %= StarDate.Millidi;
        //    data["Microdi"] = rem / StarDate.Microdi;
        //    rem %= StarDate.Microdi;
        //    data["Nanodi"] = rem / StarDate.Nanodi;
        //    rem %= StarDate.Nanodi;
        //    data["Nanodi Ticks"] = (int)rem._ticks;
        //    return data;
        //}

        //public override string ToString()
        //{
        //    return this.data("Year") + "-" + this.data("Month") + "-" + this.data("day");
        //}

        //private int data(string v)
        //{
        //    return this.data()[v];
        //}

        //private Dictionary<string, int> data()
        //{
        //    Time t = this;
        //    Dictionary<string, int> k = new Dictionary<string, int>();
        //    k.Add("Year", t / StarDate.Year);
        //    t %= StarDate.Year;
        //    k.Add("Month", t / StarDate.month);
        //    t %= StarDate.month;
        //    k.Add("day", t / StarDate.DayTime);
        //    t %= StarDate.DayTime;
        //    return k;
        //}

        //internal static Time Parse(string prim)
        //{
        //    TimeSpan time = TimeSpan.Parse(prim);
        //    return new Time(time);
        //}

        //public override bool Equals(object obj)
        //{
        //    throw new NotImplementedException();
        //}

        //public override int GetHashCode()
        //{
        //    throw new NotImplementedException();
        //}

        //public int days()
        //{
        //    return this / StarDate.DayTime;
        //}

        internal Time Negate()
        {
            return this * -1;
        }

        public string ToString(string format, IFormatProvider formatProvider)
        {
            throw new NotImplementedException();
        }

        //public string ToString(string format, IFormatProvider formatProvider)
        //{
        //    throw new NotImplementedException();
        //}

        public static Time operator *(Time t, BigInteger b)
        {
            return new Time(t._ticks * b);
        }

        public static Time operator *(BigInteger b, Time t)
        {
            return t * b;
        }

        internal void GetTimePart(out int h, out int m, out int s, out int s1)
        {
            throw new NotImplementedException();
        }
    }
}