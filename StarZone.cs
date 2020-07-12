// ==++==
// 
//   Copyright (c) Microsoft Corporation.  All rights reserved.
// 
// ==--==
/*============================================================
**
** Class: StarZone
**
**
** Purpose: 
** This class is used to represent a Dynamic TimeZone.  It
** has methods for converting a StarDate between TimeZones,
** and for reading TimeZone data from the Windows Registry
**
**
============================================================*/

using Microsoft.Win32;
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Diagnostics.Contracts;
using System.Globalization;
using System.IO;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;
using System.Runtime.Versioning;
using System.Security;
using System.Security.Permissions;
using System.Text;
using System.Threading;
//using System;
using System.Collections.Concurrent;
//using System.Collections.Generic;
using System.Linq;
using System.Net.Http.Headers;
using System.Numerics;
using static System.TimeZoneInfo;
using StarCalendar;
using System.Diagnostics.CodeAnalysis;

namespace StarCalendar
{


    //
    // StarDate uses StarZone under the hood for IsDaylightSavingTime, IsAmbiguousTime, and GetUtcOffset.
    // These StarZone APIs can throw ArgumentException when an Invalid-Time is passed in.  To avoid this
    // unwanted behavior in StarDate public APIs, StarDate internally passes the
    // StarZoneOptions.NoThrowOnInvalidTime flag to internal StarZone APIs.
    //
    // In the future we can consider exposing similar options on the public StarZone APIs if there is enough
    // demand for this alternate behavior.
    //
    [Flags]
    internal enum StarZoneOptions
    {
        None = 1,
        NoThrowOnInvalidTime = 2
    };


    //[Serializable]
    //[System.Security.Permissions.HostProtection(MayLeakOnAbort = true)]
    //[TypeForwardedFrom("System.Core, Version=3.5.0.0, Culture=Neutral, PublicKeyToken=b77a5c561934e089")]
    [Serializable]
    public class StarZone : IEquatable<StarZone>, ISerializable, IDeserializationCallback
    {

        internal string PlanetName = "Default Planet Name";
        internal Time LocalDay = StarDate.DayTime;
        public Time start = new Time(0); //atomic time that movement starts
        public double[] speeds = new double[0];
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
        //public static StarZone Terra = new StarZone("Terra", StarDate.DayTime, StarZone.Amaterasu);
        //public static StarZone Mars = new StarZone("Mars", StarDate.Sol, StarZone.Amaterasu);
        //public StarZone planet = StarZone.Terra;
        private TimeZoneInfo tz = TimeZoneInfo.Utc;
        private Time UTCOffset = new Time(0);
        private string displayName = "Default TimeZone PlanetName";
        //private int order;

        public StarZone(TimeZoneInfo tz)
        {
            this.tz = tz;
            this.displayName = tz.DisplayName;
            this.StarName = "Amaterasu";
            this.PlanetName = "Terra";
        }

        //public StarZone(TimeZoneInfo TimeZone, string v, StarZone planet) : this(TimeZone)
        //{
        //    this.displayName = v;
        //    this.planet = planet;
        //}

        public bool hasTimeZone
        {
            get
            {
                return tz != TimeZoneInfo.Utc;
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
        //public Time BaseUtcOffset
        //{
        //    get
        //    {
        //        if (this.IsTerran)
        //        {
        //            return new Time(this.TimeZone.BaseUtcOffset);
        //        }
        //        else
        //        {
        //            return UtcOffset;
        //        }
        //    }

        //}
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



        private Time distance(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return new Time(0);
                case 1:
                    //static
                    return new Time(distanceTicks[0]);
                case 2:
                    //moving
                    return new Time(distanceTicks[0]) + speeds[1] * (atomic - start);
                default:
                    throw new NotImplementedException();
            }
        }

        internal static StarZone FindSystemTimeZoneById(string v)
        {
            return (StarZone)TimeZoneInfo.FindSystemTimeZoneById(v);
        }

        public static explicit operator StarZone(TimeZoneInfo v)
        {
            return new StarZone(v);
        }

        internal static StarZone FromSerializedString(string v)
        {
            throw new NotImplementedException();
        }

        internal TimeZoneInfo.AdjustmentRule[] GetAdjustmentRules()
        {
            if (IsTerran)
            {
                return tz.GetAdjustmentRules();
            }
            else
            {
                return null;
            }
        }

        public static StarZone[] GetSystemStarZones()
        {
            return GetSystemTimeZones();
        }

        public static StarZone[] GetSystemTimeZones()
        {
            return SystemTimeZones;
            //return _sys_zones;
        }

        //internal string ToString(string v)
        //{
        //    throw new NotImplementedException();
        //}

        internal static StarDate ConvertTimeToUtc(StarDate dt, StarZone z)
        {
            dt.TickTimeZoneConvert(z);
            dt.TimeZone = UTC;
            return dt;
        }

        internal static StarDate ConvertTimeToUtc(StarDate dt)
        {
            dt.TimeZone = UTC;
            return dt;
        }

        internal static void ConvertTimeBySystemTimeZoneId(StarDate now, string v1, string v2)
        {
            throw new NotImplementedException();
        }

        internal static void ConvertTimeBySystemTimeZoneId(StarDate now, string v)
        {
            now.TimeZone = FindSystemTimeZoneById(v);
        }

        internal static void ConvertTime(StarDate now, StarZone local, StarZone uTC)
        {
            now.TimeZone = uTC;
        }

        internal static void ConvertTime(StarDate now, StarZone uTC)
        {
            now.TimeZone = uTC;
            //return now;
        }

        internal void ClearCachedData()
        {
            TimeZoneInfo.ClearCachedData();
        }

        internal Time ToRadio(Time atomic)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return atomic;
                default:
                    //I have no idea why someone would use this high an order
                    return atomic - distance(atomic);
            }
        }



        internal Time FromRadio(Time radio)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return radio;
                case 1:
                    //Static distance away from Terra
                    return radio + new Time(distanceTicks[0]);
                case 2:
                    //Moving at a constant speed relative to Terra
                    return radio + radiodistance(radio, this.speeds[1]);
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
                    return atomic;
                case 2:
                    //Moving at a constant speed relative to Terra
                    return (atomic - start) * t_observer(this.speeds[1]) + start;
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

        internal Time FromTerran(Time terran)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return terran;
                case 1:
                    //Static distance away from Terra
                    return terran;
                case 2:
                    //Moving at a constant speed relative to Terra
                    return (terran - start) * t_dilated(this.speeds[1]) + start;
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
                default:
                    //I have no idea why someone would use this high an order
                    return atomic + distance(atomic);
            }
        }

        internal Time FromArrival(Time arrival)
        {
            switch (Order)
            {
                case 0:
                    //On Terra
                    return arrival;
                case 1:
                    //Static distance away from Terra
                    return arrival - new Time(distanceTicks[0]);
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
                return BaseUtcOffset;
            }
        }

        //internal bool Sol
        //{
        //    get
        //    {
        //        return planet.Sol;
        //    }
        //}






        //public override string ToString()
        //{
        //    return base.ToString();
        //}




        // -------- SECTION: factory methods -----------------*

        //
        // CreateCustomTimeZone -
        // 
        // returns a simple TimeZoneInfo instance that does
        // not support Daylight Saving Time
        //
        public static StarZone CreateCustomTimeZone(string id, TimeSpan BaseUtcOffset)
        {
            return CreateCustomTimeZone(id, BaseUtcOffset, id, id);
        }

        public static StarZone CreateCustomTimeZone(string id, Time BaseUtcOffset)
        {
            return CreateCustomTimeZone(id, BaseUtcOffset.TimeSpan, id, id);
        }

        static public StarZone CreateCustomTimeZone(
                String id,
                TimeSpan BaseUtcOffset,
                String displayName)
        {
            return CreateCustomTimeZone(id, BaseUtcOffset, displayName, displayName);
        }

        static public StarZone CreateCustomTimeZone(
                String id,
                Time BaseUtcOffset,
                String displayName)
        {
            return CreateCustomTimeZone(id, BaseUtcOffset.TimeSpan, displayName, displayName);
        }

        public static StarZone CreateCustomTimeZone(string id, Time t, string displayname, string standard)
        {
            return CreateCustomTimeZone(id, t.TimeSpan, displayname, standard);
        }

        static public StarZone CreateCustomTimeZone(
                String id,
                TimeSpan BaseUtcOffset,
                String displayName,
                  String standardDisplayName)
        {

            TimeZoneInfo tz = TimeZoneInfo.CreateCustomTimeZone(
                           id,
                           BaseUtcOffset,
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
                TimeSpan BaseUtcOffset,
                String displayName,
                String standardDisplayName,
                String daylightDisplayName,
                TimeZoneInfo.AdjustmentRule[] adjustmentRules)
        {

            TimeZoneInfo tz = TimeZoneInfo.CreateCustomTimeZone(
                           id,
                           BaseUtcOffset,
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
                TimeSpan BaseUtcOffset,
                String displayName,
                String standardDisplayName,
                String daylightDisplayName,
                TimeZoneInfo.AdjustmentRule[] adjustmentRules,
                Boolean disableDaylightSavingTime)
        {

            TimeZoneInfo tz = TimeZoneInfo.CreateCustomTimeZone(
                            id,
                            BaseUtcOffset,
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
                if (speeds.Length > i)
                {
                    i = speeds.Length;
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
                    double[] s = new double[value];
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
                    i = 0;
                    while ((i < speeds.Length) && (i < s.Length))
                    {
                        s[i] = speeds[i];
                        i++;
                    }
                    speeds = s;
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

        public StarZone(string Name, Time LocalDay, string displayName, string standardDisplayName, string daylightDisplayName, AdjustmentRule[] adjustmentRules, bool v) : this(Name, LocalDay)
        {
            this.displayName = displayName;
            this.standardDisplayName = standardDisplayName;
            this.daylightDisplayName = daylightDisplayName;
            this.adjustmentRules = adjustmentRules;
            this.v = v;
        }

        internal object distance(StarDate now)
        {
            return distance(now.atomic);
        }



        //v is the speed of an object as a fraction of the speed of light
        //this formula only applies to constant speed moving objects
        internal static double t_observer(double v)
        {
            //t' = t / sqrt(1 - v^2/c^2)
            //t' = t / sqrt(1 - (v/c)^2)
            return 1 / Math.Sqrt(1 - Math.Pow((v / 1), 2));
        }

        internal static double t_dilated(double v)
        {
            return 1 / t_observer(v);
        }

        private Time radiodistance(Time radio, double v)
        {
            throw new NotImplementedException();
        }


        // ---- SECTION:  members for internal support ---------*
        private enum StarZoneResult
        {
            Success = 0,
            TimeZoneNotFoundException = 1,
            InvalidTimeZoneException = 2,
            SecurityException = 3
        };

        internal StarZone OffsetClone(Time value)
        {
            throw new NotImplementedException();
        }


        //#if FEATURE_WIN32_REGISTRY
        //        // registry constants for the 'Time Zones' hive
        //        //
        //        private const string c_timeZonesRegistryHive = @"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Time Zones";
        //        private const string c_timeZonesRegistryHivePermissionList = @"HKEY_LOCAL_MACHINE\" + c_timeZonesRegistryHive;
        //        private const string c_displayValue = "Display";
        //        private const string c_daylightValue = "Dlt";
        //        private const string c_standardValue = "Std";
        //        private const string c_muiDisplayValue = "MUI_Display";
        //        private const string c_muiDaylightValue = "MUI_Dlt";
        //        private const string c_muiStandardValue = "MUI_Std";
        //        private const string c_StarZoneValue = "TZI";
        //        private const string c_firstEntryValue = "FirstEntry";
        //        private const string c_lastEntryValue = "LastEntry";

        //#endif // FEATURE_WIN32_REGISTRY

        // constants for StarZone.Local and StarZone.Utc
        private const string c_utcId = "UTC";
        private const string c_localId = "Local";

        private const int c_maxKeyLength = 255;

        private const int c_regByteLength = 44;

        // Number of 100ns ticks per time unit
        private const long c_TicksPerMillisecond = 10000;
        private const long c_TicksPerSecond = c_TicksPerMillisecond * 1000;
        private const long c_TicksPerMinute = c_TicksPerSecond * 60;
        private const long c_TicksPerHour = c_TicksPerMinute * 60;
        private const long c_TicksPerDay = c_TicksPerHour * 24;
        private const long c_TicksPerDayRange = c_TicksPerDay - c_TicksPerMillisecond;

        //
        // All cached data are encapsulated in a helper class to allow consistent view even when the data are refreshed using ClearCachedData()
        //
        // For example, StarZone.Local can be cleared by another thread calling StarZone.ClearCachedData. Without the consistent snapshot, 
        // there is a chance that the internal ConvertTime calls will throw since 'source' won't be reference equal to the new StarZone.Local.
        //
        //#pragma warning disable 0420
        //class CachedData
        //{
        //    private volatile StarZone m_localTimeZone;
        //    private volatile StarZone UTC;

        //    private StarZone CreateLocal()
        //    {
        //        lock (this)
        //        {
        //            StarZone _timeZone = m_localTimeZone;
        //            if (_timeZone == null)
        //            {
        //                _timeZone = StarZone.GetLocalTimeZone(this);

        //                // this step is to break the reference equality
        //                // between StarZone.Local and a second time zone
        //                // such as "Pacific Standard Time"
        //                _timeZone = new StarZone(
        //                                    _timeZone.m_id,
        //                                    _timeZone.BaseUtcOffset,
        //                                    _timeZone.m_displayName,
        //                                    _timeZone.m_standardDisplayName,
        //                                    _timeZone.m_daylightDisplayName,
        //                                    _timeZone.m_adjustmentRules,
        //                                    false);

        //                m_localTimeZone = _timeZone;
        //            }
        //            return _timeZone;
        //        }
        //    }

        //    public StarZone Local
        //    {
        //        get
        //        {
        //            StarZone _timeZone = m_localTimeZone;
        //            if (_timeZone == null)
        //            {
        //                _timeZone = CreateLocal();
        //            }
        //            return _timeZone;
        //        }
        //    }

        private StarZone CreateUtc()
        {
            lock (this)
            {
                StarZone timeZone = UTC;
                if (timeZone == null)
                {
                    timeZone = CreateCustomTimeZone(c_utcId, Time.Zero, c_utcId, c_utcId);
                    UTC = timeZone;
                }
                return timeZone;
            }
        }

        public StarZone Utc
        {
            get
            {
                Contract.Ensures(Contract.Result<StarZone>() != null);

                StarZone timeZone = UTC;
                if (timeZone == null)
                {
                    timeZone = CreateUtc();
                }
                return timeZone;
            }
        }

        //
        // GetCorrespondingKind-
        //
        // Helper function that returns the corresponding DateTimeKind for this StarZone
        //

        public void GetObjectData(SerializationInfo info, StreamingContext context)
        {
            throw new NotImplementedException();
        }

        public void OnDeserialization(object sender)
        {
            throw new NotImplementedException();
        }

        //#if FEATURE_WIN32_REGISTRY
        //            public Dictionary<string, StarZone> m_systemTimeZones;
        //            public ReadOnlyCollection<StarZone> m_readOnlySystemTimeZones;
        //            public bool m_allSystemTimeZonesRead;

        //            [System.Security.SecuritySafeCritical]
        //            private static StarZone GetCurrentOneYearLocal() {
        //                // load the data from the OS
        //                StarZone match;

        //                Win32Native.StarZonermation StarZonermation = new Win32Native.StarZonermation();
        //                long result = UnsafeNativeMethods.GetStarZonermation(out StarZonermation);
        //                if (result == Win32Native.TIME_ZONE_ID_INVALID)
        //                    match = CreateCustomTimeZone(c_localId, Time.Zero, c_localId, c_localId);
        //                else
        //                    match = GetLocalTimeZoneFromWin32Data(StarZonermation, false);               
        //                return match;
        //            }

        //            private volatile OffsetAndRule m_oneYearLocalFromUtc;

        //            public OffsetAndRule GetOneYearLocalFromUtc(int Year) {
        //                OffsetAndRule oneYearLocFromUtc = m_oneYearLocalFromUtc;
        //                if (oneYearLocFromUtc == null || oneYearLocFromUtc.Year != Year) {
        //                    StarZone currentYear = GetCurrentOneYearLocal();
        //                    AdjustmentRule rule = currentYear.m_adjustmentRules == null ? null : currentYear.m_adjustmentRules[0];
        //                    oneYearLocFromUtc = new OffsetAndRule(Year, currentYear.BaseUtcOffset, rule);
        //                    m_oneYearLocalFromUtc = oneYearLocFromUtc;
        //                }
        //                return oneYearLocFromUtc;
        //            }

        ////#endif // FEATURE_WIN32_REGISTRY
        ////    };
        ////#pragma warning restore 0420

        //static CachedData s_cachedData = new CachedData();

        private class OffsetAndRule
        {
            public int year;
            public Time offset;
            public AdjustmentRule rule;
            public OffsetAndRule(int year, Time offset, AdjustmentRule rule)
            {
                this.year = year;
                this.offset = offset;
                this.rule = rule;
            }
        }

        //private Time BaseUtcOffset;
        private string standardDisplayName;
        private string daylightDisplayName;
        private AdjustmentRule[] adjustmentRules;
        private bool v;
        private Time basicUTCOffset;
        internal static bool NoThrowOnInvalidTime = true;
        private bool isMartian;
        private static StarZone[] martianTimeZones;
        private static StarZone[] _sys_zones;

        //private string planet;
        //private string star;

        // ---- SECTION: public properties --------------*

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

        public Time BaseUtcOffset
        {
            get
            {
                if (IsTerran)
                {
                    return (Time)tz.BaseUtcOffset;
                }
                else
                {
                    return basicUTCOffset;
                }
            }

            internal set
            {
                if (IsTerran)
                {
                    tz = TimeZoneInfo.CreateCustomTimeZone(tz.Id + "2", tz.BaseUtcOffset, tz.DisplayName + " 2.0", tz.StandardName + " 2.0", tz.DaylightName + " 2.0", tz.GetAdjustmentRules());
                }
                else
                {
                    basicUTCOffset = value;
                }

            }
        }


        public bool IsMartian { get => isMartian; private set => isMartian = value; }
        public static StarZone[] MartianTimeZones
        {
            get
            {
                if (martianTimeZones == null)
                {
                    martianTimeZones = new StarZone[24];
                    int counter = 0;
                    string line;
                    Dictionary<string, StarCulture> formats = new Dictionary<string, StarCulture>();
                    string path = "Mars.csv";
                    //int lastslash = Gedcom.LastIndexOf('/');
                    //string Filename = Gedcom.Substring(lastslash + 1);
                    //Gedson ged = new Gedson();
                    System.IO.StreamReader file = new StreamReader(path);
                    while ((line = file.ReadLine()) != null)
                    {
                        martianTimeZones[counter] = fromCSV(line);
                        counter++;
                    }
                    return martianTimeZones;
                }
                else
                {
                    return martianTimeZones;
                }
            }

        }

        public static StarZone[] SystemTimeZones
        {
            get
            {
                if (_sys_zones == null)
                {
                    var t = TimeZoneInfo.GetSystemTimeZones();
                    List<StarZone> z = new List<StarZone>();
                    int i = 0;
                    while (i < t.Count)
                    {
                        z.Add((StarZone)t[i]);
                        i++;
                    }
                    foreach (StarZone entry in MartianTimeZones)
                    {
                        z.Add(entry);
                    }
                    _sys_zones = new StarZone[z.Count];
                    i = 0;
                    while (i < _sys_zones.Length)
                    {
                        _sys_zones[i] = z[i];
                        i++;
                    }
                }
                return _sys_zones;
            }

            private set
            {
                _sys_zones = value;
            }
        }

        private static StarZone fromCSV(string line)
        {
            string[] vs = line.Split(',');
            double d = double.Parse(vs[0]);
            Time off = StarDate.HourTime * d;
            string name = vs[1];
            string planet = vs[2];
            Time LocalDay = StarDate.DayTime;
            if (planet == "Terra")
            {
                LocalDay = StarDate.DayTime;
            }
            else if (planet == "Mars")
            {
                LocalDay = StarDate.Sol;
            }
            else
            {
                double l = double.Parse(vs[3]);
                LocalDay = l * StarDate.DayTime;
            }
            string star = vs[4];
            return new StarZone(name, off, planet, LocalDay, star);
        }



        // ---- SECTION: public methods --------------*

        //
        // GetAdjustmentRules -
        //
        // returns a cloned array of AdjustmentRule objects
        //
        //public AdjustmentRule[] GetAdjustmentRules()
        //{
        //    if (m_adjustmentRules == null)
        //    {
        //        return new AdjustmentRule[0];
        //    }
        //    else
        //    {
        //        return (AdjustmentRule[])m_adjustmentRules.Clone();
        //    }
        //}


        //
        // GetAmbiguousTimeOffsets -
        //
        // returns an array of Time objects representing all of
        // possible UTC offset values for this ambiguous time
        //
        public Time[] GetAmbiguousTimeOffsets(DateTimeOffset dto)
        {
            TimeSpan[] times = tz.GetAmbiguousTimeOffsets(dto);
            Time[] times1 = new Time[times.Length];
            int i = 0;
            while (i < times.Length)
            {
                times1[i] = (Time)times[i];
                i++;
            }
            return times1;
        }



        public Time[] GetAmbiguousTimeOffsets(StarDate StarDate)
        {
            TimeSpan[] output = tz.GetAmbiguousTimeOffsets(StarDate.DateTime);
            Time[] times = new Time[output.Length];
            int i = 0;
            while (i < times.Length)
            {
                times[i] = (Time)output[i];
                i++;
            }
            return times;
        }

        //
        // GetUtcOffset -
        //
        // returns the Universal Coordinated Time (UTC) Offset
        // for the current StarZone instance.
        //
        public Time GetUtcOffset(DateTimeOffset DateTimeOffset)
        {
            return (Time)tz.GetUtcOffset(DateTimeOffset);
        }


        public Time GetUtcOffset(StarDate StarDate)
        {
            return (Time)tz.GetUtcOffset(StarDate.DateTime);
        }

        public override string ToString()
        {
            return ToString(4);
        }

        public string ToString(int tokenLen)
        {
            return ToString(tokenLen, StarDate.Now);
        }

        internal string ToString(int tokenLen, StarDate dt)
        {
            if (IsTerran && (tokenLen == 4) && !IsDaylightSavingTime(dt))
            {
                return this.DisplayName;
            }
            Offset(dt).GetTimePart(out int sign, out int h, out int m);
            Dictionary<int, string> sig = new Dictionary<int, string>() { { -1, "-" }, { 0, "" }, { 1, "+" } };

            string min = "";
            if (m != 0)
            {
                min = StarCulture.CurrentCulture.TimeSeparator;
                if (m < 10)
                {
                    min += 0;
                }
                min += m;
            }

            if (tokenLen == 1)
            {
                return sig[sign] + h + min;
            }

            string hour = "" + h;
            if (h < 10)
            {
                hour = "0" + hour;
            }

            if (tokenLen == 2)
            {
                return sig[sign] + hour + min;
            }

            if (min == "")
            {
                min = StarCulture.CurrentCulture.TimeSeparator + "00";
            }

            if (tokenLen == 3)
            {
                return sig[sign] + hour + min;
            }

            sig[0] = "+";

            if (tokenLen >= 4)
            {
                if (IsTerran && IsDaylightSavingTime(dt))
                {
                    return "(UTC" + sig[sign] + hour + min + ") " + this.daylightDisplayName;
                }
                else if (IsMartian)
                {
                    return "(MTC" + sig[sign] + hour + min + ") " + this.displayName;
                }
                else if (!IsTerran)
                {
                    return "(" + this.PlanetName[0] + "TC" + sig[sign] + hour + min + ") " + this.displayName;
                }
            }

            throw new Exception();
        }

        // Shortcut for StarZone.Local.GetUtcOffset
        //internal static Time GetLocalUtcOffset(StarDate StarDate, StarZoneOptions flags)
        //{
        //    CachedData cachedData = s_cachedData;
        //    return cachedData.Local.GetUtcOffset(StarDate, flags, cachedData);
        //}

        //internal Time GetUtcOffset(StarDate StarDate, StarZoneOptions flags)
        //{
        //    return GetUtcOffset(StarDate, flags, s_cachedData);
        //}

        //private Time GetUtcOffset(StarDate StarDate, StarZoneOptions flags, CachedData cachedData)
        //{
        //    if (StarDate.Kind == DateTimeKind.Local)
        //    {
        //        if (cachedData.GetCorrespondingKind(this) != DateTimeKind.Local)
        //        {
        //            //
        //            // normal case of converting from Local to Utc and then getting the offset from the UTC StarDate
        //            //
        //            StarDate adjustedTime = StarZone.ConvertTime(StarDate, cachedData.Local, cachedData.Utc, flags);
        //            return GetUtcOffsetFromUtc(adjustedTime, this);
        //        }

        //        //
        //        // Fall through for StarZone.Local.GetUtcOffset(date)
        //        // to handle an edge case with Invalid-Times for StarDate formatting:
        //        //
        //        // Consider the invalid PST time "2007-03-11T02:00:00.0000000-08:00"
        //        //
        //        // By directly calling GetUtcOffset instead of converting to UTC and then calling GetUtcOffsetFromUtc
        //        // the correct invalid offset of "-08:00" is returned.  In the normal case of converting to UTC as an 
        //        // interim-step, the invalid time is adjusted into a *valid* UTC time which causes a change in output:
        //        //
        //        // 1) invalid PST time "2007-03-11T02:00:00.0000000-08:00"
        //        // 2) converted to UTC "2007-03-11T10:00:00.0000000Z"
        //        // 3) offset returned  "2007-03-11T03:00:00.0000000-07:00"
        //        //
        //    }
        //    else if (StarDate.Kind == DateTimeKind.Utc)
        //    {
        //        if (cachedData.GetCorrespondingKind(this) == DateTimeKind.Utc)
        //        {
        //            return BaseUtcOffset;
        //        }
        //        else
        //        {
        //            //
        //            // passing in a UTC StarDate to a non-UTC StarZone instance is a
        //            // special Loss-Less case.
        //            //
        //            return GetUtcOffsetFromUtc(StarDate, this);
        //        }
        //    }

        //    return GetUtcOffset(StarDate, this, flags);
        //}

        //
        // IsAmbiguousTime -
        //
        // returns true if the time is during the ambiguous time period
        // for the current StarZone instance.
        //
        public Boolean IsAmbiguousTime(DateTimeOffset DateTimeOffset)
        {
            return tz.IsAmbiguousTime(DateTimeOffset);
        }


        public Boolean IsAmbiguousTime(StarDate StarDate)
        {
            return tz.IsAmbiguousTime(StarDate.DateTime);
        }

        //internal Boolean IsAmbiguousTime(StarDate StarDate, StarZoneOptions flags)
        //{
        //    if (!m_supportsDaylightSavingTime)
        //    {
        //        return false;
        //    }

        //    StarDate adjustedTime;
        //    if (StarDate.Kind == DateTimeKind.Local)
        //    {
        //        CachedData cachedData = s_cachedData;
        //        adjustedTime = StarZone.ConvertTime(StarDate, cachedData.Local, this, flags, cachedData);
        //    }
        //    else if (StarDate.Kind == DateTimeKind.Utc)
        //    {
        //        CachedData cachedData = s_cachedData;
        //        adjustedTime = StarZone.ConvertTime(StarDate, cachedData.Utc, this, flags, cachedData);
        //    }
        //    else
        //    {
        //        adjustedTime = StarDate;
        //    }

        //    AdjustmentRule rule = GetAdjustmentRuleForTime(adjustedTime);
        //    if (rule != null && rule.HasDaylightSaving)
        //    {
        //        DaylightTimeStruct daylightTime = GetDaylightTime(adjustedTime.Year, rule);
        //        return GetIsAmbiguousTime(adjustedTime, rule, daylightTime);
        //    }
        //    return false;
        //}



        //
        // IsDaylightSavingTime -
        //
        // Returns true if the time is during Daylight Saving time
        // for the current StarZone instance.
        //
        public Boolean IsDaylightSavingTime(DateTimeOffset DateTimeOffset)
        {
            return tz.IsDaylightSavingTime(DateTimeOffset);
        }


        public Boolean IsDaylightSavingTime(DateTime dateTime)
        {
            return tz.IsDaylightSavingTime(dateTime);
        }


        //
        // IsInvalidTime -
        //
        // returns true when StarDate falls into a "hole in time".
        //
        public Boolean IsInvalidTime(StarDate StarDate)
        {
            return tz.IsInvalidTime(StarDate.DateTime);
        }


        //
        // ClearCachedData -
        //
        // Clears data from static members
        //
        //static public void ClearCachedData()
        //{
        //    // Clear a fresh instance of cached data
        //    s_cachedData = new CachedData();
        //}

#if FEATURE_WIN32_REGISTRY
        //
        // ConvertTimeBySystemTimeZoneId -
        //
        // Converts the value of a StarDate object from sourceTimeZone to destinationTimeZone
        //
        static public DateTimeOffset ConvertTimeBySystemTimeZoneId(DateTimeOffset DateTimeOffset, String destinationTimeZoneId) {
            return ConvertTime(DateTimeOffset, FindSystemTimeZoneById(destinationTimeZoneId));
        }
#endif // FEATURE_WIN32_REGISTRY


#if FEATURE_WIN32_REGISTRY
        static public StarDate ConvertTimeBySystemTimeZoneId(StarDate StarDate, String destinationTimeZoneId) {
            return ConvertTime(StarDate, FindSystemTimeZoneById(destinationTimeZoneId));
        }
#endif // FEATURE_WIN32_REGISTRY

#if FEATURE_WIN32_REGISTRY
        static public StarDate ConvertTimeBySystemTimeZoneId(StarDate StarDate, String sourceTimeZoneId, String destinationTimeZoneId) {
            if (StarDate.Kind == DateTimeKind.Local && String.Compare(sourceTimeZoneId, StarZone.Local.Id, StringComparison.OrdinalIgnoreCase) == 0) {
                // StarZone.Local can be cleared by another thread calling StarZone.ClearCachedData.
                // Take snapshot of cached data to guarantee this method will not be impacted by the ClearCachedData call.
                // Without the snapshot, there is a chance that ConvertTime will throw since 'source' won't
                // be reference equal to the new StarZone.Local
                //
                CachedData cachedData = s_cachedData;
                return ConvertTime(StarDate, cachedData.Local, FindSystemTimeZoneById(destinationTimeZoneId), StarZoneOptions.None, cachedData);
            }    
            else if (StarDate.Kind == DateTimeKind.Utc && String.Compare(sourceTimeZoneId, StarZone.Utc.Id, StringComparison.OrdinalIgnoreCase) == 0) {
                // StarZone.Utc can be cleared by another thread calling StarZone.ClearCachedData.
                // Take snapshot of cached data to guarantee this method will not be impacted by the ClearCachedData call.
                // Without the snapshot, there is a chance that ConvertTime will throw since 'source' won't
                // be reference equal to the new StarZone.Utc
                //
                CachedData cachedData = s_cachedData;
                return ConvertTime(StarDate, cachedData.Utc, FindSystemTimeZoneById(destinationTimeZoneId), StarZoneOptions.None, cachedData);
            }
            else {
                return ConvertTime(StarDate, FindSystemTimeZoneById(sourceTimeZoneId), FindSystemTimeZoneById(destinationTimeZoneId));
            }
        }
#endif // FEATURE_WIN32_REGISTRY


        //
        // ConvertTime -
        //
        // Converts the value of the StarDate object from sourceTimeZone to destinationTimeZone
        //

        //static public DateTimeOffset ConvertTime(DateTimeOffset DateTimeOffset, StarZone destinationTimeZone)
        //{
        //    if (destinationTimeZone == null)
        //    {
        //        throw new ArgumentNullException("destinationTimeZone");
        //    }

        //    Contract.EndContractBlock();
        //    // calculate the destination time zone offset
        //    StarDate utcStarDate = DateTimeOffset.UtcStarDate;
        //    Time destinationOffset = GetUtcOffsetFromUtc(utcStarDate, destinationTimeZone);

        //    // check for overflow
        //    Int64 ticks = utcStarDate.Ticks + destinationOffset.Ticks;

        //    if (ticks > DateTimeOffset.MaxValue.Ticks)
        //    {
        //        return DateTimeOffset.MaxValue;
        //    }
        //    else if (ticks < DateTimeOffset.MinValue.Ticks)
        //    {
        //        return DateTimeOffset.MinValue;
        //    }
        //    else
        //    {
        //        return new DateTimeOffset(ticks, destinationOffset);
        //    }
        //}


        //static public StarDate ConvertTime(StarDate StarDate, StarZone sourceTimeZone, StarZone destinationTimeZone)
        //{
        //    return ConvertTime(StarDate, sourceTimeZone, destinationTimeZone, StarZoneOptions.None, s_cachedData);
        //}


        //static internal StarDate ConvertTime(StarDate StarDate, StarZone sourceTimeZone, StarZone destinationTimeZone, StarZoneOptions flags)
        //{
        //    return ConvertTime(StarDate, sourceTimeZone, destinationTimeZone, flags, s_cachedData);
        //}

        //static private StarDate ConvertTime(StarDate StarDate, StarZone sourceTimeZone, StarZone destinationTimeZone, StarZoneOptions flags, CachedData cachedData)
        //{
        //    if (sourceTimeZone == null)
        //    {
        //        throw new ArgumentNullException("sourceTimeZone");
        //    }

        //    if (destinationTimeZone == null)
        //    {
        //        throw new ArgumentNullException("destinationTimeZone");
        //    }
        //    Contract.EndContractBlock();

        //    DateTimeKind sourceKind = cachedData.GetCorrespondingKind(sourceTimeZone);
        //    if (((flags & StarZoneOptions.NoThrowOnInvalidTime) == 0) && (StarDate.Kind != DateTimeKind.Unspecified) && (StarDate.Kind != sourceKind))
        //    {
        //        throw new NotImplementedException(); // throw new ArgumentException(Environment.GetResourceString("Argument_ConvertMismatch"), "sourceTimeZone");
        //    }

        //    //
        //    // check to see if the StarDate is in an invalid time range.  This check
        //    // requires the current AdjustmentRule and DaylightTime - which are also
        //    // needed to calculate 'sourceOffset' in the normal conversion case.
        //    // By calculating the 'sourceOffset' here we improve the
        //    // performance for the normal case at the expense of the 'ArgumentException'
        //    // case and Loss-less Local special cases.
        //    //
        //    AdjustmentRule sourceRule = sourceTimeZone.GetAdjustmentRuleForTime(StarDate);
        //    Time sourceOffset = sourceTimeZone.BaseUtcOffset;

        //    if (sourceRule != null)
        //    {
        //        sourceOffset = sourceOffset + sourceRule.BaseUtcOffsetDelta;
        //        if (sourceRule.HasDaylightSaving)
        //        {
        //            Boolean sourceIsDaylightSavings = false;
        //            DaylightTimeStruct sourceDaylightTime = GetDaylightTime(StarDate.Year, sourceRule);

        //            // 'StarDate' might be in an invalid time range since it is in an AdjustmentRule
        //            // period that supports DST 
        //            if (((flags & StarZoneOptions.NoThrowOnInvalidTime) == 0) && GetIsInvalidTime(StarDate, sourceRule, sourceDaylightTime))
        //            {
        //                throw new NotImplementedException(); // throw new ArgumentException(Environment.GetResourceString("Argument_StarDateIsInvalid"), "StarDate");
        //            }
        //            sourceIsDaylightSavings = GetIsDaylightSavings(StarDate, sourceRule, sourceDaylightTime, flags);

        //            // adjust the sourceOffset according to the Adjustment Rule / Daylight Saving Rule
        //            sourceOffset += (sourceIsDaylightSavings ? sourceRule.DaylightDelta : Time.Zero /*FUTURE: sourceRule.StandardDelta*/);
        //        }
        //    }

        //    DateTimeKind targetKind = cachedData.GetCorrespondingKind(destinationTimeZone);

        //    // handle the special case of Loss-less Local->Local and UTC->UTC)
        //    if (StarDate.Kind != DateTimeKind.Unspecified && sourceKind != DateTimeKind.Unspecified
        //        && sourceKind == targetKind)
        //    {
        //        return StarDate;
        //    }

        //    Int64 utcTicks = StarDate.Ticks - sourceOffset.Ticks;

        //    // handle the normal case by converting from 'source' to UTC and then to 'target'
        //    Boolean isAmbiguousLocalDst = false;
        //    StarDate targetConverted = ConvertUtcToTimeZone(utcTicks, destinationTimeZone, out isAmbiguousLocalDst);

        //    if (targetKind == DateTimeKind.Local)
        //    {
        //        // Because the ticks conversion between UTC and local is lossy, we need to capture whether the 
        //        // time is in a repeated hour so that it can be passed to the StarDate constructor.
        //        return new StarDate(targetConverted.Ticks, DateTimeKind.Local, isAmbiguousLocalDst);
        //    }
        //    else
        //    {
        //        return new StarDate(targetConverted.Ticks, targetKind);
        //    }
        //}



        //
        // ConvertTimeFromUtc -
        //
        // Converts the value of a StarDate object from Coordinated Universal Time (UTC) to
        // the destinationTimeZone.
        //
        //static public StarDate ConvertTimeFromUtc(StarDate StarDate, StarZone destinationTimeZone)
        //{
        //    CachedData cachedData = s_cachedData;
        //    return ConvertTime(StarDate, cachedData.Utc, destinationTimeZone, StarZoneOptions.None, cachedData);
        //}


        //
        // ConvertTimeToUtc -
        //
        // Converts the value of a StarDate object to Coordinated Universal Time (UTC).
        //
        //static public StarDate ConvertTimeToUtc(StarDate StarDate)
        //{
        //    if (StarDate.Kind == DateTimeKind.Utc)
        //    {
        //        return StarDate;
        //    }
        //    CachedData cachedData = s_cachedData;
        //    return ConvertTime(StarDate, cachedData.Local, cachedData.Utc, StarZoneOptions.None, cachedData);
        //}





        //
        // IEquatable.Equals -
        //
        // returns value equality.  Equals does not compare any localizable
        // String objects (DisplayName, StandardName, DaylightName).
        //
        public bool Equals([AllowNull] StarZone other)
        {
            return (tz.Equals(other.tz)) && (PlanetName == other.PlanetName) && (LocalDay == other.LocalDay) && (Order == other.Order) && (start == other.start) && (speeds == other.speeds)
                && (distanceTicks == other.distanceTicks) && (polar == other.polar) && (azimuthal == other.azimuthal) && (StarName == other.StarName)
                && (BaseUtcOffset == other.BaseUtcOffset) && (displayName == other.displayName);
            //return (other != null && String.Compare(this.m_id, other.m_id, StringComparison.OrdinalIgnoreCase) == 0 && HasSameRules(other));
        }

        public override bool Equals(object obj)
        {
            StarZone tzi = obj as StarZone;
            if (null == tzi)
            {
                return false;
            }
            return Equals(tzi);
        }

        //    
        // FromSerializedString -
        //
        //static public StarZone FromSerializedString(string source)
        //{
        //    if (source == null)
        //    {
        //        throw new ArgumentNullException("source");
        //    }
        //    if (source.Length == 0)
        //    {
        //        throw new NotImplementedException(); // throw new ArgumentException(Environment.GetResourceString("Argument_InvalidSerializedString", source), "source");
        //    }
        //    Contract.EndContractBlock();

        //    return StringSerializer.GetDeserializedStarZone(source);
        //}


        //
        // GetHashCode -
        //
        //public override int GetHashCode()
        //{
        //    return m_id.ToUpper(CultureInfo.InvariantCulture).GetHashCode();
        //}

        internal static StarZone FindTimeZone(string prim)
        {
            throw new NotImplementedException();
        }


#if FEATURE_WIN32_REGISTRY
        //
        // GetSystemTimeZones -
        //
        // returns a ReadOnlyCollection<StarZone> containing all valid TimeZone's
        // from the local machine.  The entries in the collection are sorted by
        // 'DisplayName'.
        //
        // This method does *not* throw TimeZoneNotFoundException or
        // InvalidTimeZoneException.
        //
        // <SecurityKernel Critical="True" Ring="0">
        // <Asserts Name="Imperative: System.Security.PermissionSet" />
        // </SecurityKernel>
        [System.Security.SecuritySafeCritical]  // auto-generated
        [ResourceExposure(ResourceScope.None)]
        static public ReadOnlyCollection<StarZone> GetSystemTimeZones() {

            CachedData cachedData = s_cachedData;

            lock (cachedData) {
                if (cachedData.m_readOnlySystemTimeZones == null) {
                    PermissionSet permSet = new PermissionSet(PermissionState.None);
                    permSet.AddPermission(new RegistryPermission(RegistryPermissionAccess.Read, c_timeZonesRegistryHivePermissionList));
                    permSet.Assert();
               
                    using (RegistryKey reg = Registry.LocalMachine.OpenSubKey(
                                        c_timeZonesRegistryHive,
#if FEATURE_MACL
                                        RegistryKeyPermissionCheck.Default,
                                        System.Security.AccessControl.RegistryRights.ReadKey
#else
                                        false
#endif
                                        )) {

                        if (reg != null) {
                            foreach (string keyName in reg.GetSubKeyNames()) {
                                StarZone value;
                                Exception ex;
                                TryGetTimeZone(keyName, false, out value, out ex, cachedData);  // populate the cache
                            }
                        }
                        cachedData.m_allSystemTimeZonesRead = true;
                    }

                    List<StarZone> list;
                    if (cachedData.m_systemTimeZones != null) {
                        // return a collection of the cached system time zones
                        list = new List<StarZone>(cachedData.m_systemTimeZones.Values);
                    }
                    else {
                        // return an empty collection
                        list = new List<StarZone>();
                    }

                    // sort and copy the StarZone's into a ReadOnlyCollection for the user
                    list.Sort(new StarZoneComparer());

                    cachedData.m_readOnlySystemTimeZones = new ReadOnlyCollection<StarZone>(list);
                }          
            }
            return cachedData.m_readOnlySystemTimeZones;
        }
#endif // FEATURE_WIN32_REGISTRY


        //
        // HasSameRules -
        //
        // Value equality on the "adjustmentRules" array
        //
        public Boolean HasSameRules(StarZone other)
        {
            if (other == null)
            {
                throw new ArgumentNullException("other");
            }

            return this.tz.HasSameRules(other.tz);
        }

        //
        // Local -
        //
        // returns a StarZone instance that represents the local time on the machine.
        // Accessing this property may throw InvalidTimeZoneException or COMException
        // if the machine is in an unstable or corrupt state.
        //



        //
        // ToSerializedString -
        //
        // "StarZone"           := StarZone Data;[AdjustmentRule Data 1];...;[AdjustmentRule Data N]
        //
        // "StarZone Data"      := <m_id>;<BaseUtcOffset>;<m_displayName>;
        //                          <m_standardDisplayName>;<m_daylightDispayName>;
        //
        // "AdjustmentRule Data" := <DateStart>;<DateEnd>;<DaylightDelta>;
        //                          [TransitionTime Data DST Start]
        //                          [TransitionTime Data DST End]
        //
        // "TransitionTime Data" += <DaylightStartTimeOfDat>;<Month>;<Week>;<DayOfWeek>;<Day>
        //
        public String ToSerializedString()
        {
            return StringSerializer.GetSerializedString(this);
        }


        //
        // ToString -
        //
        // returns the DisplayName: 
        // "(GMT-08:00) Pacific Time (US & Canada); Tijuana"
        //
        //public override string ToString()
        //{
        //    return this.ToString(5);
        //}


        //
        // Utc -
        //
        // returns a StarZone instance that represents Universal Coordinated Time (UTC)
        //
        //static public StarZone Utc
        //{
        //    get
        //    {
        //        Contract.Ensures(Contract.Result<StarZone>() != null);
        //        return s_cachedData.Utc;
        //    }
        //}

        //public StarZone UTC
        //{
        //    get
        //    {
        //        return utcTimeZone;
        //    }

        //    private set
        //    {
        //        utcTimeZone = value;
        //    }
        //}


        // -------- SECTION: constructors -----------------*
        // 
        // StarZone -
        //
        // private ctor
        //
        //[System.Security.SecurityCritical]  // auto-generated
        //private StarZone(Win32Native.StarZonermation zone, Boolean dstDisabled)
        //{

        //    if (String.IsNullOrEmpty(zone.StandardName))
        //    {
        //        m_id = c_localId;  // the ID must contain at least 1 character - initialize m_id to "Local"
        //    }
        //    else
        //    {
        //        m_id = zone.StandardName;
        //    }
        //    BaseUtcOffset = new Time(0, -(zone.Bias), 0);

        //    if (!dstDisabled)
        //    {
        //        // only create the adjustment rule if DST is enabled
        //        Win32Native.RegistryStarZonermation regZone = new Win32Native.RegistryStarZonermation(zone);
        //        AdjustmentRule rule = CreateAdjustmentRuleFromStarZonermation(regZone, StarDate.MinValue.Date, StarDate.MaxValue.Date, zone.Bias);
        //        if (rule != null)
        //        {
        //            m_adjustmentRules = new AdjustmentRule[1];
        //            m_adjustmentRules[0] = rule;
        //        }
        //    }

        //    ValidateStarZone(m_id, BaseUtcOffset, m_adjustmentRules, out m_supportsDaylightSavingTime);
        //    m_displayName = zone.StandardName;
        //    m_standardDisplayName = zone.StandardName;
        //    m_daylightDisplayName = zone.DaylightName;
        //}

        //private StarZone(
        //        String id,
        //        Time BaseUtcOffset,
        //        String displayName,
        //        String standardDisplayName,
        //        String daylightDisplayName,
        //        AdjustmentRule[] adjustmentRules,
        //        Boolean disableDaylightSavingTime)
        //{

        //    Boolean adjustmentRulesSupportDst;
        //    ValidateStarZone(id, BaseUtcOffset, adjustmentRules, out adjustmentRulesSupportDst);

        //    if (!disableDaylightSavingTime && adjustmentRules != null && adjustmentRules.Length > 0)
        //    {
        //        m_adjustmentRules = (AdjustmentRule[])adjustmentRules.Clone();
        //    }

        //    m_id = id;
        //    BaseUtcOffset = BaseUtcOffset;
        //    m_displayName = displayName;
        //    m_standardDisplayName = standardDisplayName;
        //    m_daylightDisplayName = (disableDaylightSavingTime ? null : daylightDisplayName);
        //    m_supportsDaylightSavingTime = adjustmentRulesSupportDst && !disableDaylightSavingTime;
        //}

        // -------- SECTION: factory methods -----------------*

        //
        // CreateCustomTimeZone -
        // 
        // returns a simple StarZone instance that does
        // not support Daylight Saving Time
        //
        //static public StarZone CreateCustomTimeZone(
        //        String id,
        //        Time BaseUtcOffset,
        //        String displayName,
        //          String standardDisplayName)
        //{

        //    return new StarZone(
        //                   id,
        //                   BaseUtcOffset,
        //                   displayName,
        //                   standardDisplayName,
        //                   standardDisplayName,
        //                   null,
        //                   false);
        //}

        //
        // CreateCustomTimeZone -
        // 
        // returns a StarZone instance that may
        // support Daylight Saving Time
        //
        static public StarZone CreateCustomTimeZone(
                String id,
                Time BaseUtcOffset,
                String displayName,
                String standardDisplayName,
                String daylightDisplayName,
                AdjustmentRule[] adjustmentRules)
        {

            return new StarZone(
                           id,
                           BaseUtcOffset,
                           displayName,
                           standardDisplayName,
                           daylightDisplayName,
                           adjustmentRules,
                           false);
        }


        //
        // CreateCustomTimeZone -
        // 
        // returns a StarZone instance that may
        // support Daylight Saving Time
        //
        // This class factory method is identical to the
        // StarZone private constructor
        //
        static public StarZone CreateCustomTimeZone(
                String id,
                Time BaseUtcOffset,
                String displayName,
                String standardDisplayName,
                String daylightDisplayName,
                AdjustmentRule[] adjustmentRules,
                Boolean disableDaylightSavingTime)
        {

            return new StarZone(
                            id,
                            BaseUtcOffset,
                            displayName,
                            standardDisplayName,
                            daylightDisplayName,
                            adjustmentRules,
                            disableDaylightSavingTime);
        }



        // ----- SECTION: private serialization instance methods  ----------------*

#if FEATURE_SERIALIZATION
        void IDeserializationCallback.OnDeserialization(Object sender) {
            try {
                Boolean adjustmentRulesSupportDst;
                ValidateStarZone(m_id, BaseUtcOffset, m_adjustmentRules, out adjustmentRulesSupportDst);

                if (adjustmentRulesSupportDst != m_supportsDaylightSavingTime) {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_CorruptField", "SupportsDaylightSavingTime"));
                }
            }
            catch (ArgumentException e) {
                throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), e);
            }
            catch (InvalidTimeZoneException e) {
                throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), e);
            }
        }


        [System.Security.SecurityCritical]  // auto-generated_required
        void ISerializable.GetObjectData(SerializationInfo info, StreamingContext context) {
            if (info == null) {
                throw new ArgumentNullException("info");
            }
            Contract.EndContractBlock();

            info.AddValue("Id", m_id);
            info.AddValue("DisplayName", m_displayName);
            info.AddValue("StandardName", m_standardDisplayName);
            info.AddValue("DaylightName", m_daylightDisplayName);
            info.AddValue("BaseUtcOffset", BaseUtcOffset);
            info.AddValue("AdjustmentRules", m_adjustmentRules);
            info.AddValue("SupportsDaylightSavingTime", m_supportsDaylightSavingTime);
        }

        
        StarZone(SerializationInfo info, StreamingContext context) {
            if (info == null) {
                throw new ArgumentNullException("info");
            }

            m_id                  = (String)info.GetValue("Id", typeof(String));
            m_displayName         = (String)info.GetValue("DisplayName", typeof(String));
            m_standardDisplayName = (String)info.GetValue("StandardName", typeof(String));
            m_daylightDisplayName = (String)info.GetValue("DaylightName", typeof(String));
            BaseUtcOffset       = (Time)info.GetValue("BaseUtcOffset", typeof(Time));
            m_adjustmentRules     = (AdjustmentRule[])info.GetValue("AdjustmentRules", typeof(AdjustmentRule[]));
            m_supportsDaylightSavingTime = (Boolean)info.GetValue("SupportsDaylightSavingTime", typeof(Boolean));
        }
#endif



        // ----- SECTION: internal instance utility methods ----------------*


        // assumes StarDate is in the current time zone's time
        //private AdjustmentRule GetAdjustmentRuleForTime(StarDate StarDate)
        //{
        //    if (m_adjustmentRules == null || m_adjustmentRules.Length == 0)
        //    {
        //        return null;
        //    }

        //    // Only check the whole-date portion of the StarDate -
        //    // This is because the AdjustmentRule DateStart & DateEnd are stored as
        //    // Date-only values {4/2/2006 - 10/28/2006} but actually represent the
        //    // time span {4/2/2006@00:00:00.00000 - 10/28/2006@23:59:59.99999}
        //    StarDate date = StarDate.Date;

        //    for (int i = 0; i < m_adjustmentRules.Length; i++)
        //    {
        //        if (m_adjustmentRules[i].DateStart <= date && m_adjustmentRules[i].DateEnd >= date)
        //        {
        //            return m_adjustmentRules[i];
        //        }
        //    }

        //    return null;
        //}



        // ----- SECTION: internal static utility methods ----------------*

        //
        // CheckDaylightSavingTimeNotSupported -
        //
        // Helper function to check if the current StarZonermation struct does not support DST.  This
        // check returns true when the DaylightDate == StandardDate
        //
        // This check is only meant to be used for "Local".
        //
        [System.Security.SecurityCritical]  // auto-generated
                                            //static private Boolean CheckDaylightSavingTimeNotSupported(Win32Native.StarZonermation _timeZone)
                                            //{
                                            //    return (_timeZone.DaylightDate.Year == _timeZone.StandardDate.Year
                                            //            && _timeZone.DaylightDate.Month == _timeZone.StandardDate.Month
                                            //            && _timeZone.DaylightDate.DayOfWeek == _timeZone.StandardDate.DayOfWeek
                                            //            && _timeZone.DaylightDate.Day == _timeZone.StandardDate.Day
                                            //            && _timeZone.DaylightDate.Hour == _timeZone.StandardDate.Hour
                                            //            && _timeZone.DaylightDate.Minute == _timeZone.StandardDate.Minute
                                            //            && _timeZone.DaylightDate.Second == _timeZone.StandardDate.Second
                                            //            && _timeZone.DaylightDate.Millisecond == _timeZone.StandardDate.Millisecond);
                                            //}


        //
        // ConvertUtcToTimeZone -
        //
        // Helper function that converts a StarDate from UTC into the destinationTimeZone
        //
        // * returns StarDate.MaxValue when the converted value is too large
        // * returns StarDate.MinValue when the converted value is too small
        //
        //static private StarDate ConvertUtcToTimeZone(Int64 ticks, StarZone destinationTimeZone, out Boolean isAmbiguousLocalDst)
        //{
        //    StarDate utcConverted;
        //    StarDate localConverted;

        //    // utcConverted is used to calculate the UTC offset in the destinationTimeZone
        //    if (ticks > StarDate.MaxValue.Ticks)
        //    {
        //        utcConverted = StarDate.MaxValue;
        //    }
        //    else if (ticks < StarDate.MinValue.Ticks)
        //    {
        //        utcConverted = StarDate.MinValue;
        //    }
        //    else
        //    {
        //        utcConverted = new StarDate(ticks);
        //    }

        //    // verify the time is between MinValue and MaxValue in the new time zone
        //    Time offset = GetUtcOffsetFromUtc(utcConverted, destinationTimeZone, out isAmbiguousLocalDst);
        //    ticks += offset.Ticks;

        //    if (ticks > StarDate.MaxValue.Ticks)
        //    {
        //        localConverted = StarDate.MaxValue;
        //    }
        //    else if (ticks < StarDate.MinValue.Ticks)
        //    {
        //        localConverted = StarDate.MinValue;
        //    }
        //    else
        //    {
        //        localConverted = new StarDate(ticks);
        //    }
        //    return localConverted;
        //}


        //
        // CreateAdjustmentRuleFromStarZonermation-
        //
        // Converts a Win32Native.RegistryStarZonermation (REG_TZI_FORMAT struct) to an AdjustmentRule
        //
        //[System.Security.SecurityCritical]  // auto-generated
        //static private AdjustmentRule CreateAdjustmentRuleFromStarZonermation(Win32Native.RegistryStarZonermation StarZonermation, StarDate startDate, StarDate endDate, int defaultBaseUtcOffset)
        //{
        //    AdjustmentRule rule;
        //    bool supportsDst = (StarZonermation.StandardDate.Month != 0);

        //    if (!supportsDst)
        //    {
        //        if (StarZonermation.Bias == defaultBaseUtcOffset)
        //        {
        //            // this rule will not contain any information to be used to adjust dates. just ignore it
        //            return null;
        //        }

        //        return rule = AdjustmentRule.CreateAdjustmentRule(
        //            startDate,
        //            endDate,
        //            Time.Zero, // no daylight saving transition
        //            TransitionTime.CreateFixedDateRule(StarDate.MinValue, 1, 1),
        //            TransitionTime.CreateFixedDateRule(StarDate.MinValue.AddMilliseconds(1), 1, 1),
        //            new Time(0, defaultBaseUtcOffset - StarZonermation.Bias, 0));  // Bias delta is all what we need from this rule
        //    }

        //
        // Create an AdjustmentRule with TransitionTime objects
        //
        //    TransitionTime daylightTransitionStart;
        //    if (!TransitionTimeFromStarZonermation(StarZonermation, out daylightTransitionStart, true /* start date */))
        //    {
        //        return null;
        //    }

        //    TransitionTime daylightTransitionEnd;
        //    if (!TransitionTimeFromStarZonermation(StarZonermation, out daylightTransitionEnd, false /* end date */))
        //    {
        //        return null;
        //    }

        //    if (daylightTransitionStart.Equals(daylightTransitionEnd))
        //    {
        //        // this happens when the time zone does support DST but the OS has DST disabled
        //        return null;
        //    }

        //    rule = AdjustmentRule.CreateAdjustmentRule(
        //        startDate,
        //        endDate,
        //        new Time(0, -StarZonermation.DaylightBias, 0),
        //        (TransitionTime)daylightTransitionStart,
        //        (TransitionTime)daylightTransitionEnd,
        //        new Time(0, defaultBaseUtcOffset - StarZonermation.Bias, 0));

        //    return rule;
        //}


#if FEATURE_WIN32_REGISTRY
        //
        // FindIdFromStarZonermation -
        //
        // Helper function that searches the registry for a time zone entry
        // that matches the StarZonermation struct
        //
        [System.Security.SecuritySafeCritical]  // auto-generated
        [ResourceExposure(ResourceScope.None)]
        static private String FindIdFromStarZonermation(Win32Native.StarZonermation timeZone, out Boolean dstDisabled) {
            dstDisabled = false;

            try {
                PermissionSet permSet = new PermissionSet(PermissionState.None);
                permSet.AddPermission(new RegistryPermission(RegistryPermissionAccess.Read, c_timeZonesRegistryHivePermissionList));
                permSet.Assert();

                using (RegistryKey key = Registry.LocalMachine.OpenSubKey(
                                  c_timeZonesRegistryHive,
#if FEATURE_MACL
                                  RegistryKeyPermissionCheck.Default,
                                  System.Security.AccessControl.RegistryRights.ReadKey
#else
                                  false
#endif
                                  )) {

                    if (key == null) {
                        return null;
                    }
                    foreach (string keyName in key.GetSubKeyNames()) {
                        if (TryCompareStarZonermationToRegistry(timeZone, keyName, out dstDisabled)) {
                            return keyName;
                        }
                    }
                }
            }
            finally {
                PermissionSet.RevertAssert();
            }
            return null;
        }
#endif // FEATURE_WIN32_REGISTRY


        //
        // GetDaylightTime -
        //
        // Helper function that returns a DaylightTime from a Year and AdjustmentRule
        //
        //static private DaylightTimeStruct GetDaylightTime(Int32 Year, AdjustmentRule rule)
        //{
        //    Time delta = rule.DaylightDelta;
        //    StarDate startTime = TransitionTimeToStarDate(Year, rule.DaylightTransitionStart);
        //    StarDate endTime = TransitionTimeToStarDate(Year, rule.DaylightTransitionEnd);
        //    return new DaylightTimeStruct(startTime, endTime, delta);
        //}

        //public void GetObjectData(SerializationInfo info, StreamingContext context)
        //{
        //    throw new NotImplementedException();
        //}

        //public void OnDeserialization(object sender)
        //{
        //    throw new NotImplementedException();
        //}

        //
        // GetIsDaylightSavings -
        //
        // Helper function that checks if a given StarDate is in Daylight Saving Time (DST)
        // This function assumes the StarDate and AdjustmentRule are both in the same time zone
        //



        //
        // GetIsDaylightSavingsFromUtc -
        //
        // Helper function that checks if a given StarDate is in Daylight Saving Time (DST)
        // This function assumes the StarDate is in UTC and AdjustmentRule is in a different time zone
        //



        /*============================================================
        **
        ** Class: StarZone.AdjustmentRule
        **
        **
        ** Purpose: 
        ** This class is used to represent a Dynamic TimeZone.  It
        ** has methods for converting a StarDate to UTC from local time
        ** and to local time from UTC and methods for getting the 
        ** standard name and daylight name of the time zone.  
        **
        **
        ============================================================*/
        sealed private class StringSerializer
        {

            // ---- SECTION: private members  -------------*
            private enum State
            {
                Escaped = 0,
                NotEscaped = 1,
                StartOfToken = 2,
                EndOfLine = 3
            }

            private String m_serializedText;
            private int m_currentTokenStartIndex;
            private State m_state;

            // the majority of the strings contained in the OS time zones fit in 64 chars
            private const int initialCapacityForString = 64;
            private const char esc = '\\';
            private const char sep = ';';
            private const char lhs = '[';
            private const char rhs = ']';
            private const string escString = "\\";
            private const string sepString = ";";
            private const string lhsString = "[";
            private const string rhsString = "]";
            private const string escapedEsc = "\\\\";
            private const string escapedSep = "\\;";
            private const string escapedLhs = "\\[";
            private const string escapedRhs = "\\]";
            private const string StarDateFormat = "MM:dd:yyyy";
            private const string timeOfDayFormat = "HH:mm:ss.FFF";


            // ---- SECTION: public static methods --------------*

            //
            // GetSerializedString -
            //
            // static method that creates the custom serialized string
            // representation of a StarZone instance
            //
            static public String GetSerializedString(StarZone zone)
            {
                throw new NotImplementedException();
            }


            //
            // GetDeserializedStarZone -
            //
            // static method that instantiates a StarZone from a custom serialized
            // string
            //
            static public StarZone GetDeserializedStarZone(String source)
            {
                StringSerializer s = new StringSerializer(source);

                String id = s.GetNextStringValue(false);
                Time BaseUtcOffset = s.GetNextTimeValue(false);
                String displayName = s.GetNextStringValue(false);
                String standardName = s.GetNextStringValue(false);
                String daylightName = s.GetNextStringValue(false);
                AdjustmentRule[] rules = s.GetNextAdjustmentRuleArrayValue(false);

                try
                {
                    return StarZone.CreateCustomTimeZone(id, BaseUtcOffset, displayName, standardName, daylightName, rules);
                }
                catch (ArgumentException)
                {
                    throw new NotImplementedException(); // throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), ex);
                }
                catch (InvalidTimeZoneException)
                {
                    throw new NotImplementedException(); //throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), ex);
                }
            }

            private AdjustmentRule[] GetNextAdjustmentRuleArrayValue(bool v)
            {
                throw new NotImplementedException();
            }

            // ---- SECTION: public instance methods --------------*


            // -------- SECTION: constructors -----------------*

            //
            // StringSerializer -
            //
            // private constructor - used by GetDeserializedStarZone()
            //
            private StringSerializer(String str)
            {
                m_serializedText = str;
                m_state = State.StartOfToken;
            }



            // ----- SECTION: internal static utility methods ----------------*

            //
            // SerializeSubstitute -
            //
            // returns a new string with all of the reserved sub-strings escaped
            //
            // ";" -> "\;"
            // "[" -> "\["
            // "]" -> "\]"
            // "\" -> "\\"
            //
            static private String SerializeSubstitute(String text)
            {
                text = text.Replace(escString, escapedEsc);
                text = text.Replace(lhsString, escapedLhs);
                text = text.Replace(rhsString, escapedRhs);
                return text.Replace(sepString, escapedSep);
            }


            //
            // SerializeTransitionTime -
            //
            // Helper method to serialize a StarZone.TransitionTime object
            //
            static private void SerializeTransitionTime(TransitionTime time, StringBuilder serializedText)
            {
                serializedText.Append(lhs);
                Int32 fixedDate = (time.IsFixedDateRule ? 1 : 0);
                serializedText.Append(fixedDate.ToString(CultureInfo.InvariantCulture));
                serializedText.Append(sep);

                if (time.IsFixedDateRule)
                {
                    serializedText.Append(SerializeSubstitute(time.TimeOfDay.ToString(timeOfDayFormat, StarCulture.InvariantCulture.FormatProvider)));
                    serializedText.Append(sep);
                    serializedText.Append(SerializeSubstitute(time.Month.ToString(CultureInfo.InvariantCulture)));
                    serializedText.Append(sep);
                    serializedText.Append(SerializeSubstitute(time.Day.ToString(CultureInfo.InvariantCulture)));
                    serializedText.Append(sep);
                }
                else
                {
                    serializedText.Append(SerializeSubstitute(time.TimeOfDay.ToString(timeOfDayFormat, StarCulture.InvariantCulture.FormatProvider)));
                    serializedText.Append(sep);
                    serializedText.Append(SerializeSubstitute(time.Month.ToString(CultureInfo.InvariantCulture)));
                    serializedText.Append(sep);
                    serializedText.Append(SerializeSubstitute(time.Week.ToString(CultureInfo.InvariantCulture)));
                    serializedText.Append(sep);
                    serializedText.Append(SerializeSubstitute(((int)time.DayOfWeek).ToString(CultureInfo.InvariantCulture)));
                    serializedText.Append(sep);
                }
                serializedText.Append(rhs);
            }

            //
            // VerifyIsEscapableCharacter -
            //
            // Helper function to determine if the passed in string token is allowed to be preceeded by an escape sequence token
            //
            static private void VerifyIsEscapableCharacter(char c)
            {
                if (c != esc && c != sep && c != lhs && c != rhs)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidEscapeSequence", c));
                }
            }

            // ----- SECTION: internal instance utility methods ----------------*

            //
            // SkipVersionNextDataFields -
            //
            // Helper function that reads past "v.Next" data fields.  Receives a "depth" parameter indicating the
            // current relative nested bracket depth that m_currentTokenStartIndex is at.  The function ends
            // successfully when "depth" returns to zero (0).
            //
            //
            private void SkipVersionNextDataFields(Int32 depth /* starting depth in the nested brackets ('[', ']')*/)
            {
                if (m_currentTokenStartIndex < 0 || m_currentTokenStartIndex >= m_serializedText.Length)
                {
                    throw new NotImplementedException(); //throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }
                State tokenState = State.NotEscaped;

                // walk the serialized text, building up the token as we go...
                for (int i = m_currentTokenStartIndex; i < m_serializedText.Length; i++)
                {
                    if (tokenState == State.Escaped)
                    {
                        VerifyIsEscapableCharacter(m_serializedText[i]);
                        tokenState = State.NotEscaped;
                    }
                    else if (tokenState == State.NotEscaped)
                    {
                        switch (m_serializedText[i])
                        {
                            case esc:
                                tokenState = State.Escaped;
                                break;

                            case lhs:
                                depth++;
                                break;
                            case rhs:
                                depth--;
                                if (depth == 0)
                                {
                                    m_currentTokenStartIndex = i + 1;
                                    if (m_currentTokenStartIndex >= m_serializedText.Length)
                                    {
                                        m_state = State.EndOfLine;
                                    }
                                    else
                                    {
                                        m_state = State.StartOfToken;
                                    }
                                    return;
                                }
                                break;

                            case '\0':
                                // invalid character
                                throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));

                            default:
                                break;
                        }
                    }
                }

                throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            }


            //
            // GetNextStringValue -
            //
            // Helper function that reads a string token from the serialized text.  The function
            // updates the m_currentTokenStartIndex to point to the next token on exit.  Also m_state
            // is set to either State.StartOfToken or State.EndOfLine on exit.
            //
            // The function takes a parameter "canEndWithoutSeparator".  
            //
            // * When set to 'false' the function requires the string token end with a ";".
            // * When set to 'true' the function requires that the string token end with either
            //   ";", State.EndOfLine, or "]".  In the case that "]" is the terminal case the
            //   m_currentTokenStartIndex is left pointing at index "]" to allow the caller to update
            //   its depth logic.
            //
            private String GetNextStringValue(Boolean canEndWithoutSeparator)
            {

                // first verify the internal state of the object
                if (m_state == State.EndOfLine)
                {
                    if (canEndWithoutSeparator)
                    {
                        return null;
                    }
                    else
                    {
                        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                    }
                }
                if (m_currentTokenStartIndex < 0 || m_currentTokenStartIndex >= m_serializedText.Length)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }
                State tokenState = State.NotEscaped;
                StringBuilder token = StringBuilderCache.Acquire(initialCapacityForString);

                // walk the serialized text, building up the token as we go...
                for (int i = m_currentTokenStartIndex; i < m_serializedText.Length; i++)
                {
                    if (tokenState == State.Escaped)
                    {
                        VerifyIsEscapableCharacter(m_serializedText[i]);
                        token.Append(m_serializedText[i]);
                        tokenState = State.NotEscaped;
                    }
                    else if (tokenState == State.NotEscaped)
                    {
                        switch (m_serializedText[i])
                        {
                            case esc:
                                tokenState = State.Escaped;
                                break;

                            case lhs:
                                // '[' is an unexpected character
                                throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));

                            case rhs:
                                if (canEndWithoutSeparator)
                                {
                                    // if ';' is not a required terminal then treat ']' as a terminal
                                    // leave m_currentTokenStartIndex pointing to ']' so our callers can handle
                                    // this special case
                                    m_currentTokenStartIndex = i;
                                    m_state = State.StartOfToken;
                                    return token.ToString();
                                }
                                else
                                {
                                    // ']' is an unexpected character
                                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                                }

                            case sep:
                                m_currentTokenStartIndex = i + 1;
                                if (m_currentTokenStartIndex >= m_serializedText.Length)
                                {
                                    m_state = State.EndOfLine;
                                }
                                else
                                {
                                    m_state = State.StartOfToken;
                                }
                                return StringBuilderCache.GetStringAndRelease(token);

                            case '\0':
                                // invalid character
                                throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));

                            default:
                                token.Append(m_serializedText[i]);
                                break;
                        }
                    }
                }
                //
                // we are at the end of the line
                //
                if (tokenState == State.Escaped)
                {
                    // we are at the end of the serialized text but we are in an escaped state
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidEscapeSequence", String.Empty));
                }

                if (!canEndWithoutSeparator)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }
                m_currentTokenStartIndex = m_serializedText.Length;
                m_state = State.EndOfLine;
                return StringBuilderCache.GetStringAndRelease(token);
            }

            //
            // GetNextStarDateValue -
            //
            // Helper function to read a StarDate token.  Takes a boolean "canEndWithoutSeparator"
            // and a "format" string.
            //
            //private StarDate GetNextStarDateValue(Boolean canEndWithoutSeparator, string format)
            //{
            //    String token = GetNextStringValue(canEndWithoutSeparator);
            //    StarDate time;
            //    if (!StarDate.TryParseExact(token, format, StarCulture.InvariantCulture.FormatProvider, StarDateStyles.None, out time))
            //    {
            //        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //    }
            //    return time;
            //}

            //
            // GetNextTimeValue -
            //
            // Helper function to read a StarDate token.  Takes a boolean "canEndWithoutSeparator".
            //
            private Time GetNextTimeValue(Boolean canEndWithoutSeparator)
            {
                Int32 token = GetNextInt32Value(canEndWithoutSeparator);

                try
                {
                    return new Time(0 /* hours */, token /* minutes */, 0 /* seconds */);
                }
                catch (ArgumentOutOfRangeException)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), e);
                }
            }


            //
            // GetNextInt32Value -
            //
            // Helper function to read an Int32 token.  Takes a boolean "canEndWithoutSeparator".
            //
            private Int32 GetNextInt32Value(Boolean canEndWithoutSeparator)
            {
                String token = GetNextStringValue(canEndWithoutSeparator);
                Int32 value;
                if (!Int32.TryParse(token, NumberStyles.AllowLeadingSign /* "[sign]digits" */, CultureInfo.InvariantCulture, out value))
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }
                return value;
            }


            //
            // GetNextAdjustmentRuleArrayValue -
            //
            // Helper function to read an AdjustmentRule[] token.  Takes a boolean "canEndWithoutSeparator".
            //
            //private AdjustmentRule[] GetNextAdjustmentRuleArrayValue(Boolean canEndWithoutSeparator)
            //{
            //    List<AdjustmentRule> rules = new List<AdjustmentRule>(1);
            //    int count = 0;

            //    // individual AdjustmentRule array elements do not require semicolons
            //    AdjustmentRule rule = GetNextAdjustmentRuleValue(true);
            //    while (rule != null)
            //    {
            //        rules.Add(rule);
            //        count++;

            //        rule = GetNextAdjustmentRuleValue(true);
            //    }

            //    if (!canEndWithoutSeparator)
            //    {
            //        // the AdjustmentRule array must end with a separator
            //        if (m_state == State.EndOfLine)
            //        {
            //            throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //        }
            //        if (m_currentTokenStartIndex < 0 || m_currentTokenStartIndex >= m_serializedText.Length)
            //        {
            //            throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //        }
            //    }

            //    return (count != 0 ? rules.ToArray() : null);
            //}

            //
            // GetNextAdjustmentRuleValue -
            //
            // Helper function to read an AdjustmentRule token.  Takes a boolean "canEndWithoutSeparator".
            //
            //private AdjustmentRule GetNextAdjustmentRuleValue(Boolean canEndWithoutSeparator)
            //{
            //    // first verify the internal state of the object
            //    if (m_state == State.EndOfLine)
            //    {
            //        if (canEndWithoutSeparator)
            //        {
            //            return null;
            //        }
            //        else
            //        {
            //            throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //        }
            //    }

            //    if (m_currentTokenStartIndex < 0 || m_currentTokenStartIndex >= m_serializedText.Length)
            //    {
            //        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //    }

            //    // check to see if the very first token we see is the separator
            //    if (m_serializedText[m_currentTokenStartIndex] == sep)
            //    {
            //        return null;
            //    }

            //    // verify the current token is a left-hand-side marker ("[")
            //    if (m_serializedText[m_currentTokenStartIndex] != lhs)
            //    {
            //        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //    }
            //    m_currentTokenStartIndex++;

            //    StarDate dateStart = GetNextStarDateValue(false, StarDateFormat);
            //    StarDate dateEnd = GetNextStarDateValue(false, StarDateFormat);
            //    Time daylightDelta = GetNextTimeValue(false);
            //    TransitionTime daylightStart = GetNextTransitionTimeValue(false);
            //    TransitionTime daylightEnd = GetNextTransitionTimeValue(false);
            //    Time BaseUtcOffsetDelta = Time.Zero;
            //    // verify that the string is now at the right-hand-side marker ("]") ...

            //    if (m_state == State.EndOfLine || m_currentTokenStartIndex >= m_serializedText.Length)
            //    {
            //        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //    }

            //    // Check if we have BaseUtcOffsetDelta in the serialized string and then deserialize it
            //    if ((m_serializedText[m_currentTokenStartIndex] >= '0' && m_serializedText[m_currentTokenStartIndex] <= '9') ||
            //        m_serializedText[m_currentTokenStartIndex] == '-' || m_serializedText[m_currentTokenStartIndex] == '+')
            //    {
            //        BaseUtcOffsetDelta = GetNextTimeValue(false);
            //    }

            //    if (m_state == State.EndOfLine || m_currentTokenStartIndex >= m_serializedText.Length)
            //    {
            //        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
            //    }

            //    if (m_serializedText[m_currentTokenStartIndex] != rhs)
            //    {
            //        // skip ahead of any "v.Next" data at the end of the AdjustmentRule
            //        //
            //        // 


            //        SkipVersionNextDataFields(1);
            //    }
            //    else
            //    {
            //        m_currentTokenStartIndex++;
            //    }

            //    // create the AdjustmentRule from the deserialized fields ...

            //    AdjustmentRule rule;
            //    try
            //    {
            //        rule = AdjustmentRule.CreateAdjustmentRule(dateStart, dateEnd, daylightDelta, daylightStart, daylightEnd, BaseUtcOffsetDelta);
            //    }
            //    catch (ArgumentException e)
            //    {
            //        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), e);
            //    }

            //    // finally set the state to either EndOfLine or StartOfToken for the next caller
            //    if (m_currentTokenStartIndex >= m_serializedText.Length)
            //    {
            //        m_state = State.EndOfLine;
            //    }
            //    else
            //    {
            //        m_state = State.StartOfToken;
            //    }
            //    return rule;
            //}


            //
            // GetNextTransitionTimeValue -
            //
            // Helper function to read a TransitionTime token.  Takes a boolean "canEndWithoutSeparator".
            //
            private TransitionTime GetNextTransitionTimeValue(Boolean canEndWithoutSeparator)
            {

                // first verify the internal state of the object

                if (m_state == State.EndOfLine
                    || (m_currentTokenStartIndex < m_serializedText.Length
                        && m_serializedText[m_currentTokenStartIndex] == rhs))
                {
                    //
                    // we are at the end of the line or we are starting at a "]" character
                    //
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }

                if (m_currentTokenStartIndex < 0 || m_currentTokenStartIndex >= m_serializedText.Length)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }

                // verify the current token is a left-hand-side marker ("[")

                if (m_serializedText[m_currentTokenStartIndex] != lhs)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }
                m_currentTokenStartIndex++;

                Int32 isFixedDate = GetNextInt32Value(false);

                if (isFixedDate != 0 && isFixedDate != 1)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }

                TransitionTime transition;

                StarDate timeOfDay = GetNextStarDateValue(false, timeOfDayFormat);
                timeOfDay = new StarDate(1, 1, 1, timeOfDay.Hour, timeOfDay.Minute, timeOfDay.Second, timeOfDay.Millisecond);

                Int32 month = GetNextInt32Value(false);

                if (isFixedDate == 1)
                {
                    Int32 day = GetNextInt32Value(false);

                    try
                    {
                        transition = TransitionTime.CreateFixedDateRule(timeOfDay, month, day);
                    }
                    catch (ArgumentException)
                    {
                        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), e);
                    }
                }
                else
                {
                    Int32 week = GetNextInt32Value(false);
                    Int32 dayOfWeek = GetNextInt32Value(false);

                    try
                    {
                        transition = TransitionTime.CreateFloatingDateRule(timeOfDay, month, week, (DayOfWeek)dayOfWeek);
                    }
                    catch (ArgumentException)
                    {
                        throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"), e);
                    }

                }

                // verify that the string is now at the right-hand-side marker ("]") ...

                if (m_state == State.EndOfLine || m_currentTokenStartIndex >= m_serializedText.Length)
                {
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }

                if (m_serializedText[m_currentTokenStartIndex] != rhs)
                {
                    // skip ahead of any "v.Next" data at the end of the AdjustmentRule
                    //
                    // 


                    SkipVersionNextDataFields(1);
                }
                else
                {
                    m_currentTokenStartIndex++;
                }

                // check to see if the string is now at the separator (";") ...
                Boolean sepFound = false;
                if (m_currentTokenStartIndex < m_serializedText.Length
                    && m_serializedText[m_currentTokenStartIndex] == sep)
                {
                    // handle the case where we ended on a ";"
                    m_currentTokenStartIndex++;
                    sepFound = true;
                }

                if (!sepFound && !canEndWithoutSeparator)
                {
                    // we MUST end on a separator
                    throw new NotImplementedException(); //throw new SerializationException(Environment.GetResourceString("Serialization_InvalidData"));
                }


                // finally set the state to either EndOfLine or StartOfToken for the next caller
                if (m_currentTokenStartIndex >= m_serializedText.Length)
                {
                    m_state = State.EndOfLine;
                }
                else
                {
                    m_state = State.StartOfToken;
                }
                return transition;
            }

            private StarDate GetNextStarDateValue(bool v, string timeOfDayFormat)
            {
                throw new NotImplementedException();
            }
        }

        private class StarZoneComparer : System.Collections.Generic.IComparer<StarZone>
        {
            int System.Collections.Generic.IComparer<StarZone>.Compare(StarZone x, StarZone y)
            {
                // sort by BaseUtcOffset first and by DisplayName second - this is similar to the Windows Date/Time control panel
                int comparison = x.BaseUtcOffset.CompareTo(y.BaseUtcOffset);
                return comparison == 0 ? String.Compare(x.DisplayName, y.DisplayName, StringComparison.Ordinal) : comparison;
            }
        }

        public override int GetHashCode()
        {
            throw new NotImplementedException();
        }

        protected StarZone(SerializationInfo serializationInfo, StreamingContext streamingContext)
        {
            throw new NotImplementedException();
        }

        public StarZone(string Name, Time Off, string planet, Time LocalDay, string star) : this(Name, LocalDay)
        {
            this.PlanetName = planet;
            this.LocalDay = LocalDay;
            this.StarName = star;
            this.BaseUtcOffset = Off;
        }
    }
} // StarZone
