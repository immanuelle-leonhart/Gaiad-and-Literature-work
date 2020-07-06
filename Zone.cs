using System;
using System.Collections.Generic;
using System.Numerics;
using static System.TimeZoneInfo;

namespace StarCalendar
{
    public class Zone
    {
        public PlanetZone planet = PlanetZone.Terra;
        private TimeZoneInfo tz = TimeZoneInfo.Utc;
        private TimeSpanInfo baseUtcOffset = new TimeSpanInfo(0);
        public static Zone Local = new Zone(TimeZoneInfo.Local);
        public static Zone UTC = new Zone(TimeZoneInfo.Utc, "UTC", PlanetZone.Terra);
        private string displayName = "Default TimeZone Name";

        public Zone(TimeZoneInfo tz)
        {
            this.tz = tz;
            this.displayName = tz.DisplayName;
        }

        public Zone(TimeZoneInfo tz, string v, PlanetZone planet) : this(tz)
        {
            this.displayName = v;
            this.planet = planet;
        }

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
                return this.planet.Name == "Terra";
            }
        }
        public TimeSpanInfo Day
        {
            get
            {
                return this.planet.LocalDay;
            }

            internal set
            {
                this.planet.LocalDay = value;
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

        internal static Zone FindTimeZone(string v)
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
            throw new NotImplementedException();
        }

        internal bool Sol
        {
            get
            {
                return planet.Sol;
            }
        }

        internal TimeSpanInfo GetOffset(StarDate now)
        {
            throw new NotImplementedException();
        }

        internal void ClearCachedData()
        {
            throw new NotImplementedException();
        }

        internal static void ConvertTime(StarDate now, Zone uTC)
        {
            throw new NotImplementedException();
        }

        internal static void ConvertTime(StarDate now, Zone local, Zone uTC)
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

        internal static StarDate ConvertTimeToUtc(StarDate dt, Zone z)
        {
            throw new NotImplementedException();
        }

        internal static Zone FindSystemTimeZoneById(string v)
        {
            throw new NotImplementedException();
        }

        internal static Zone FromSerializedString(string v)
        {
            throw new NotImplementedException();
        }

        internal TimeZoneInfo.AdjustmentRule[] GetAdjustmentRules()
        {
            throw new NotImplementedException();
        }

        internal static Zone[] GetSystemTimeZones()
        {
            throw new NotImplementedException();
        }

        internal bool HasSameRules(Zone uTC)
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
        public static Zone CreateCustomTimeZone(string id, TimeSpan BaseUTCOffset)
        {
            return CreateCustomTimeZone(id, BaseUTCOffset, id, id);
        }

        public static Zone CreateCustomTimeZone(string id, TimeSpanInfo BaseUTCOffset)
        {
            return CreateCustomTimeZone(id, BaseUTCOffset.TimeSpan, id, id);
        }

        static public Zone CreateCustomTimeZone(
                String id,
                TimeSpan baseUtcOffset,
                String displayName)
        {
            return CreateCustomTimeZone(id, baseUtcOffset, displayName, displayName);
        }

        static public Zone CreateCustomTimeZone(
                String id,
                TimeSpanInfo baseUtcOffset,
                String displayName)
        {
            return CreateCustomTimeZone(id, baseUtcOffset.TimeSpan, displayName, displayName);
        }

        public static Zone CreateCustomTimeZone(string id, TimeSpanInfo t, string displayname, string standard)
        {
            return CreateCustomTimeZone(id, t.TimeSpan, displayname, standard);
        }

        static public Zone CreateCustomTimeZone(
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
            return new Zone(tz);
        }

        //
        // CreateCustomTimeZone -
        // 
        // returns a TimeZoneInfo instance that may
        // support Daylight Saving Time
        //
        static public Zone CreateCustomTimeZone(
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
                           false); return new Zone(tz);
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
        static public Zone CreateCustomTimeZone(
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
                            disableDaylightSavingTime); return new Zone(tz);
        }

        internal static TimeSpanInfo GetLocalUtcOffset(StarDate starDate)
        {
            throw new NotImplementedException();
        }

        internal static TimeSpanInfo GetLocalUtcOffset(StarDate dt, bool noThrowOnInvalidTime)
        {
            throw new NotImplementedException();
        }
    }
}