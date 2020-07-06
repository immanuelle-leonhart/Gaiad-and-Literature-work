using System;
using System.Collections.Generic;
using System.Numerics;
using static System.TimeZoneInfo;

namespace StarCalendar
{
    public class StarZone
    {
        internal string PlanetName = "Default Planet Name";
        internal TimeSpanInfo LocalDay = c.Day;
        public StarDate startDate = new StarDate(0); //atomic time that movement starts
        public List<BigInteger> distanceTicks = new List<BigInteger> { 0 }; //position, speed, acceleration, etc
        public List<double> polar = new List<double> { 0 }; //position, speed, acceleration, etc
        public List<double> azimuthal = new List<double> { 0 }; //position, speed, acceleration, etc
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
        private TimeSpanInfo baseUtcOffset = new TimeSpanInfo(0);
        private string displayName = "Default TimeZone PlanetName";

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
        public TimeSpanInfo Day
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
        public TimeSpanInfo BaseUtcOffset
        {
            get
            {
                if (this.IsTerran)
                {
                    return new TimeSpanInfo(this.tz.BaseUtcOffset);
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

        internal TimeSpanInfo ToRadio(TimeSpanInfo atomic)
        {
            throw new NotImplementedException();
        }

        internal TimeSpanInfo FromRadio(TimeSpanInfo value)
        {
            throw new NotImplementedException();
        }

        internal TimeSpanInfo ToTerran(TimeSpanInfo atomic)
        {
            throw new NotImplementedException();
        }

        internal TimeSpanInfo FromTerran(TimeSpanInfo value)
        {
            throw new NotImplementedException();
        }

        internal TimeSpanInfo ToArrival(TimeSpanInfo atomic)
        {
            throw new NotImplementedException();
        }

        internal TimeSpanInfo FromArrival(TimeSpanInfo value)
        {
            throw new NotImplementedException();
        }

        internal TimeSpanInfo Offset(DateTime dateTime)
        {
            if (SupportsDaylightSavingTime)
            {
                return new TimeSpanInfo(tz.GetUtcOffset(dateTime));
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

        internal TimeSpanInfo GetOffset(StarDate now)
        {
            throw new NotImplementedException();
        }

        internal void ClearCachedData()
        {
            throw new NotImplementedException();
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

        public static StarZone CreateCustomTimeZone(string id, TimeSpanInfo BaseUTCOffset)
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
                TimeSpanInfo baseUtcOffset,
                String displayName)
        {
            return CreateCustomTimeZone(id, baseUtcOffset.TimeSpan, displayName, displayName);
        }

        public static StarZone CreateCustomTimeZone(string id, TimeSpanInfo t, string displayname, string standard)
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

        internal static TimeSpanInfo GetLocalUtcOffset(StarDate starDate)
        {
            throw new NotImplementedException();
        }

        internal static TimeSpanInfo GetLocalUtcOffset(StarDate dt, bool noThrowOnInvalidTime)
        {
            throw new NotImplementedException();
        }

        public StarZone(string Name, TimeSpanInfo LocalDay)
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

        public double[] cartesian()
        {
            double x = (long)distanceTicks[0] * Math.Sin(polar[0]) * Math.Cos(azimuthal[0]);
            double y = (long)distanceTicks[0] * Math.Sin(polar[0]) * Math.Sin(azimuthal[0]);
            double z = (long)distanceTicks[0] * Math.Cos(polar[0]);
            return new double[] { x, y, z };
        }

        public StarZone(StarDate startDate, List<BigInteger> distanceTicks, List<double> polar, List<double> azimuthal)
        {
            this.startDate = startDate;
            this.distanceTicks = distanceTicks;
            this.polar = polar;
            this.azimuthal = azimuthal;
        }

        public StarZone(string name)
        {
            this.StarName = name;
        }

        internal object distance_at_time(StarDate now)
        {
            throw new NotImplementedException();
        }
    }
}