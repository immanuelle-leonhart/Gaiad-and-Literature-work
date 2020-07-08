using SpaceCalendar;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using static System.TimeZoneInfo;

namespace StarCalendar
{
    public class StarZone
    {
        internal string PlanetName = "Default Planet Name";
        internal Time LocalDay = c.Day;
        public Time start = new Time(0); //atomic time that movement starts
        public BigInteger[] distanceTicks = new BigInteger[0]; //position, speed, acceleration, etc
        public double[] polar = new double[0]; //position, speed, acceleration, etc
        public double[] azimuthal = new double[0]; //position, speed, acceleration, etc
        public string StarName = "Default Star System Name";
        public static StarZone Terra;
        public static StarZone Mars;
        public static StarZone Amaterasu;
        public static StarZone Local = new StarZone(TimeZoneInfo.Local);
        public static StarZone UTC = new StarZone(TimeZoneInfo.Utc);
        //public static StarZone Amaterasu = new StarZone("Amaterasu");
        //internal StarZone Sun = StarZone.Amaterasu;
        //public static StarZone Terra = new StarZone("Terra", c.Day, StarZone.Amaterasu);
        //public static StarZone Mars = new StarZone("Mars", c.Sol, StarZone.Amaterasu);
        //public StarZone planet = StarZone.Terra;
        private TimeZoneInfo tz = TimeZoneInfo.Utc;
        private Time baseUtcOffset = new Time(0);
        private string displayName = "Default TimeZone PlanetName";
        //private int order;

        public StarZone(TimeZoneInfo tz)
        {
            this.tz = tz;
            this.displayName = tz.DisplayName;
            this.StarName = "Amaterasu";
            this.PlanetName = "Terra";
        }

        //public StarZone(TimeZoneInfo tz, string v, StarZone planet) : this(tz)
        //{
        //    this.displayName = v;
        //    this.planet = planet;
        //}

        public bool hasTimeZone
        {
            get
            {
                return tz == TimeZoneInfo.Utc;
            }
        }
        public bool IsTerran
        {
            get
            {
                return this.PlanetName == "Terra";
            }
        }
        public Time Day
        {
            get
            {
                return this.LocalDay;
            }

            internal set
            {
                this.LocalDay = value;
            }
        }
        public Time BaseUtcOffset
        {
            get
            {
                if (this.IsTerran)
                {
                    return new Time(this.tz.BaseUtcOffset);
                }
                else
                {
                    return baseUtcOffset;
                }
            }

        }
        public string DaylightName
        {
            get
            {
                return this.tz.DaylightName;
            }
        }
        public string DisplayName
        {
            get
            {
                if (this.IsTerran) { return tz.DisplayName; }
                else
                {
                    return this.displayName;
                }
            }
        }
        public string Id
        {
            get
            {
                if (this.IsTerran) { return tz.Id; }
                else
                {
                    return this.displayName;
                }
            }
        }
        public string StandardName
        {
            get
            {
                if (this.IsTerran) { return tz.StandardName; }
                else
                {
                    return this.displayName;
                }
            }
        }
        public bool SupportsDaylightSavingTime
        {
            get
            {
                if (this.IsTerran) { return tz.SupportsDaylightSavingTime; }
                else
                {
                    return false;
                }
            }
        }

        internal static StarZone FindTimeZone(string v)
        {
            throw new NotImplementedException();
        }

        private Time distance(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return new Time(0);
                default:
                    throw new NotImplementedException();
            }
        }

        internal Time ToRadio(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return atomic;
                case 1:
                    return atomic - distance(atomic); ;
                case 2:
                    //Moving at a constant speed relative to Terra
                    throw new NotImplementedException();
                case 3:
                    //accelerating
                    throw new NotImplementedException();
                case 4:
                    //Jerk (changing rate of acceleration)
                    throw new NotImplementedException();
                case 5:
                    //Snap
                    throw new NotImplementedException();
                case 6:
                    //Crackle
                    throw new NotImplementedException();
                case 7:
                    //Pop
                    throw new NotImplementedException();
                default:
                    //I have no idea why someone would use this high an order
                    throw new NotImplementedException();
            }
        }



        internal Time FromRadio(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return atomic;
                case 1:
                    //Static distance away from Terra
                    throw new NotImplementedException();
                case 2:
                    //Moving at a constant speed relative to Terra
                    throw new NotImplementedException();
                case 3:
                    //accelerating
                    throw new NotImplementedException();
                case 4:
                    //Jerk (changing rate of acceleration)
                    throw new NotImplementedException();
                case 5:
                    //Snap
                    throw new NotImplementedException();
                case 6:
                    //Crackle
                    throw new NotImplementedException();
                case 7:
                    //Pop
                    throw new NotImplementedException();
                default:
                    //I have no idea why someone would use this high an order
                    throw new NotImplementedException();
            }
        }

        internal Time ToTerran(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return atomic;
                case 1:
                    //Static distance away from Terra
                    throw new NotImplementedException();
                case 2:
                    //Moving at a constant speed relative to Terra
                    throw new NotImplementedException();
                case 3:
                    //accelerating
                    throw new NotImplementedException();
                case 4:
                    //Jerk (changing rate of acceleration)
                    throw new NotImplementedException();
                case 5:
                    //Snap
                    throw new NotImplementedException();
                case 6:
                    //Crackle
                    throw new NotImplementedException();
                case 7:
                    //Pop
                    throw new NotImplementedException();
                default:
                    //I have no idea why someone would use this high an order
                    throw new NotImplementedException();
            }
        }

        internal Time FromTerran(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return atomic;
                case 1:
                    //Static distance away from Terra
                    throw new NotImplementedException();
                case 2:
                    //Moving at a constant speed relative to Terra
                    throw new NotImplementedException();
                case 3:
                    //accelerating
                    throw new NotImplementedException();
                case 4:
                    //Jerk (changing rate of acceleration)
                    throw new NotImplementedException();
                case 5:
                    //Snap
                    throw new NotImplementedException();
                case 6:
                    //Crackle
                    throw new NotImplementedException();
                case 7:
                    //Pop
                    throw new NotImplementedException();
                default:
                    //I have no idea why someone would use this high an order
                    throw new NotImplementedException();
            }
        }

        internal Time ToArrival(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return atomic;
                case 1:
                    //Static distance away from Terra
                    throw new NotImplementedException();
                case 2:
                    //Moving at a constant speed relative to Terra
                    throw new NotImplementedException();
                case 3:
                    //accelerating
                    throw new NotImplementedException();
                case 4:
                    //Jerk (changing rate of acceleration)
                    throw new NotImplementedException();
                case 5:
                    //Snap
                    throw new NotImplementedException();
                case 6:
                    //Crackle
                    throw new NotImplementedException();
                case 7:
                    //Pop
                    throw new NotImplementedException();
                default:
                    //I have no idea why someone would use this high an order
                    throw new NotImplementedException();
            }
        }

        internal Time FromArrival(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return atomic;
                case 1:
                    //Static distance away from Terra
                    throw new NotImplementedException();
                case 2:
                    //Moving at a constant speed relative to Terra
                    throw new NotImplementedException();
                case 3:
                    //accelerating
                    throw new NotImplementedException();
                case 4:
                    //Jerk (changing rate of acceleration)
                    throw new NotImplementedException();
                case 5:
                    //Snap
                    throw new NotImplementedException();
                case 6:
                    //Crackle
                    throw new NotImplementedException();
                case 7:
                    //Pop
                    throw new NotImplementedException();
                default:
                    //I have no idea why someone would use this high an order
                    throw new NotImplementedException();
            }
        }

        internal Time Offset(StarDate now)
        {
            return Offset(now.DateTime);
        }

        internal Time Offset(DateTime dateTime)
        {
            if (SupportsDaylightSavingTime)
            {
                return new Time(tz.GetUtcOffset(dateTime));
            }
            else
            {
                return baseUtcOffset;
            }
        }

        //internal bool Sol
        //{
        //    get
        //    {
        //        return planet.Sol;
        //    }
        //}



        internal void ClearCachedData()
        {
            //throw new NotImplementedException();
        }

        internal static void ConvertTime(StarDate now, StarZone uTC)
        {
            throw new NotImplementedException();
        }

        internal static void ConvertTime(StarDate now, StarZone local, StarZone uTC)
        {
            throw new NotImplementedException();
        }

        internal static void ConvertTimeBySystemTimeZoneId(StarDate now, string v)
        {
            throw new NotImplementedException();
        }

        internal static void ConvertTimeBySystemTimeZoneId(StarDate now, string v1, string v2)
        {
            throw new NotImplementedException();
        }

        internal static StarDate ConvertTimeToUtc(StarDate dt)
        {
            throw new NotImplementedException();
        }

        internal static StarDate ConvertTimeToUtc(StarDate dt, StarZone z)
        {
            throw new NotImplementedException();
        }

        internal static StarZone FindSystemTimeZoneById(string v)
        {
            throw new NotImplementedException();
        }

        internal static StarZone FromSerializedString(string v)
        {
            throw new NotImplementedException();
        }

        internal TimeZoneInfo.AdjustmentRule[] GetAdjustmentRules()
        {
            throw new NotImplementedException();
        }

        internal static StarZone[] GetSystemTimeZones()
        {
            throw new NotImplementedException();
        }

        internal bool HasSameRules(StarZone uTC)
        {
            throw new NotImplementedException();
        }

        internal bool IsDaylightSavingTime(StarDate dt)
        {
            throw new NotImplementedException();
        }

        internal string ToSerializedString()
        {
            throw new NotImplementedException();
        }

        public override string ToString()
        {
            return base.ToString();
        }

        internal string ToString(string v)
        {
            throw new NotImplementedException();
        }


        // -------- SECTION: factory methods -----------------*

        //
        // CreateCustomTimeZone -
        // 
        // returns a simple TimeZoneInfo instance that does
        // not support Daylight Saving Time
        //
        public static StarZone CreateCustomTimeZone(string id, TimeSpan BaseUTCOffset)
        {
            return CreateCustomTimeZone(id, BaseUTCOffset, id, id);
        }

        public static StarZone CreateCustomTimeZone(string id, Time BaseUTCOffset)
        {
            return CreateCustomTimeZone(id, BaseUTCOffset.TimeSpan, id, id);
        }

        static public StarZone CreateCustomTimeZone(
                String id,
                TimeSpan baseUtcOffset,
                String displayName)
        {
            return CreateCustomTimeZone(id, baseUtcOffset, displayName, displayName);
        }

        static public StarZone CreateCustomTimeZone(
                String id,
                Time baseUtcOffset,
                String displayName)
        {
            return CreateCustomTimeZone(id, baseUtcOffset.TimeSpan, displayName, displayName);
        }

        public static StarZone CreateCustomTimeZone(string id, Time t, string displayname, string standard)
        {
            return CreateCustomTimeZone(id, t.TimeSpan, displayname, standard);
        }

        static public StarZone CreateCustomTimeZone(
                String id,
                TimeSpan baseUtcOffset,
                String displayName,
                  String standardDisplayName)
        {

            TimeZoneInfo tz = TimeZoneInfo.CreateCustomTimeZone(
                           id,
                           baseUtcOffset,
                           displayName,
                           standardDisplayName,
                           standardDisplayName,
                           null,
                           false);
            return new StarZone(tz);
        }

        //
        // CreateCustomTimeZone -
        // 
        // returns a TimeZoneInfo instance that may
        // support Daylight Saving Time
        //
        static public StarZone CreateCustomTimeZone(
                String id,
                TimeSpan baseUtcOffset,
                String displayName,
                String standardDisplayName,
                String daylightDisplayName,
                AdjustmentRule[] adjustmentRules)
        {

            TimeZoneInfo tz = TimeZoneInfo.CreateCustomTimeZone(
                           id,
                           baseUtcOffset,
                           displayName,
                           standardDisplayName,
                           daylightDisplayName,
                           adjustmentRules,
                           false); return new StarZone(tz);
        }


        //
        // CreateCustomTimeZone -
        // 
        // returns a TimeZoneInfo instance that may
        // support Daylight Saving Time
        //
        // This class factory method is identical to the
        // TimeZoneInfo private constructor
        //
        static public StarZone CreateCustomTimeZone(
                String id,
                TimeSpan baseUtcOffset,
                String displayName,
                String standardDisplayName,
                String daylightDisplayName,
                AdjustmentRule[] adjustmentRules,
                Boolean disableDaylightSavingTime)
        {

            TimeZoneInfo tz = TimeZoneInfo.CreateCustomTimeZone(
                            id,
                            baseUtcOffset,
                            displayName,
                            standardDisplayName,
                            daylightDisplayName,
                            adjustmentRules,
                            disableDaylightSavingTime); return new StarZone(tz);
        }

        internal static Time GetLocalUtcOffset(StarDate starDate)
        {
            return starDate.offset;
        }

        internal static Time GetLocalUtcOffset(StarDate dt, bool noThrowOnInvalidTime)
        {
            return dt.offset;
        }

        public StarZone(string Name, Time LocalDay)
        {
            this.PlanetName = Name;
            this.LocalDay = LocalDay;
            //this.Sun = Sun;
        }

        //public bool Sol
        //{
        //    get
        //    {
        //        return this.Sun.Sol;
        //    }
        //}

        internal static StarZone get(string v)
        {
            throw new NotImplementedException();
        }



        public bool Sol
        {
            get
            {
                return StarName == "Amaterasu";
            }
        }

        public int Order
        {
            get
            {
                int i = 0;
                if (distanceTicks.Length > i)
                {
                    i = distanceTicks.Length;
                }
                if (polar.Length > i)
                {
                    i = polar.Length;
                }
                if (azimuthal.Length > i)
                {
                    i = azimuthal.Length;
                }
                return i;
            }

            private set
            {
                if (value == Order)
                {
                    //Do nothing
                }
                else
                {
                    BigInteger[] t = new BigInteger[value];
                    double[] p = new double[value];
                    double[] a = new double[value];
                    int i = 0;
                    while ((i < distanceTicks.Length) && (i < t.Length))
                    {
                        t[i] = distanceTicks[i];
                        i++;
                    }
                    distanceTicks = t;
                    i = 0;
                    while ((i < polar.Length) && (i < p.Length))
                    {
                        p[i] = polar[i];
                        i++;
                    }
                    polar = p;
                    i = 0;
                    while ((i < azimuthal.Length) && (i < a.Length))
                    {
                        a[i] = azimuthal[i];
                        i++;
                    }
                    azimuthal = a;
                }
            }
        }

        public double[] cartesian()
        {
            double x = (long)distanceTicks[0] * Math.Sin(polar[0]) * Math.Cos(azimuthal[0]);
            double y = (long)distanceTicks[0] * Math.Sin(polar[0]) * Math.Sin(azimuthal[0]);
            double z = (long)distanceTicks[0] * Math.Cos(polar[0]);
            return new double[] { x, y, z };
        }

        public StarZone(Time startDate, BigInteger[] distanceTicks, double[] polar, double[] azimuthal)
        {
            this.start = startDate;
            this.distanceTicks = distanceTicks;
            this.polar = polar;
            this.azimuthal = azimuthal;
        }

        public StarZone(string name)
        {
            this.StarName = name;
        }

        internal object distance(StarDate now)
        {
            return distance(now.atomic);
        }

        internal StarZone OffsetClone(Time value)
        {
            throw new NotImplementedException();
        }

        //internal static Time GetLocalUtcOffset(StarDate now)
        //{
        //    throw new NotImplementedException();
        //}
    }
}