using StarLib;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;

namespace StarLib
{
    internal static class c
    {
        //internal static List<StarCulture> formats = getformats();
        private static Time Tick = new Time(1);
        private static Time Millisecond = new Time(10000);
        private static int TicksPerMillisecond = 10000;
        private static Time Second = Millisecond * 1000;
        private static int TicksPerSecond = TicksPerMillisecond * 1000;
        private static Time Minute = Second * 60;
        private static int TicksPerMinute = TicksPerSecond * 60;
        private static Time Hour = Minute * 60;
        private static int TicksPerHour = TicksPerMinute * 60;
        private static Time Day = Hour * 24;
        private static int TicksPerDay = TicksPerHour * 24;
        private static Time Decidi = Day / 10;
        private static Time Centidi = Day / 100;
        private static Time Millidi = Day / 1000;
        private static Time Microdi = Day / 1000000;
        private static Time Nanodi = Day / 1000000000; //Only Metric Time needed
        private static Time Sol = 1.02749125 * Day;
        private static Time week = Day * 7;
        private static Time month = week * 4;
        private static Time Year = week * 52;
        private static Time Leap = Year + week;
        private static Time DoubleLeap = Leap + week;
        private static Time Sixyear = Year * 6 + week; //6 years, 313 weeks;
        private static Time Seventy_Eight = Sixyear * 13 + week; //78 years, 4070 weeks;
        private static Time AverageYear = Day * 365.256410256;
        //internal static Time SiderealYear = Day * 365.25636;
        private static Time SiderealYear = Seventy_Eight / 78;
        private static Time k = SiderealYear * 1000;
        private static Time m = k * 1000;
        private static Time b = m * 1000;
        private static Time a = 200 * m;
        private static StarDate manu = StarDate.AbstractDate(14 * b);
        private static StarDate maya = manu + 154 * Seventy_Eight; //10k BC + 154 * 78 = 12012
        private static DateTime maya_net = new DateTime(2011, 12, 26); //2011-12-26
        //internal static DateTime new_year_12018 = new DateTime(2017, 12, 18, 0, 0, 0, DateTimeKind.Utc); //Sunday Saggittarius 1, 12013
        //internal static StarDate Trump1 = manu + 154 * Seventy_Eight + 6 * Year; //new_year_12018, Dec 18 2017
        //internal static StarDate y2k = manu + (12 * k);
        private static StarDate netstart = maya - new Time(maya_net.Ticks);
        private static StarDate julian = maya - 2455921 * Day;
        private static Time tr = b * 1000;



        //internal static Dictionary<string, StarZone> Planets = new Dictionary<string, StarZone>();
        //internal static Dictionary<string, StarZone> StarSystems = new Dictionary<string, StarZone>();


        //internal static Dictionary<string, NaturalCycle> CachedCycles = new Dictionary<string, NaturalCycle>();
        internal static readonly Time LunarMonth = Day * 29.53059;
        internal static readonly Time MercurialYear = (87.9691 * Day);
        internal static readonly Time MercurialDay = (58.646 * Day);
        internal static readonly Time VenusianYear = (224.701 * Day);
        internal static readonly Time VenusianSolation = (116.75 * Day);
        internal static readonly Time MartianSol = (1.02749125 * Day);
        internal static readonly Time MartianYear = (686.971 * Day);
        internal static readonly Time PhobosMonth = (0.31891023 * Day);
        internal static readonly Time DeimosMonth = (1.263 * Day);
        internal static readonly Time CereanYear = (1683.14570801 * Day);
        internal static readonly Time JovianYear = (4332.59 * Day);
        internal static readonly Time IoanMonth = (42.47665 * Hour);
        internal static readonly Time EuropanMonth = (85.29825 * Hour);
        internal static readonly Time GanymedeanMonth = (171.99327 * Hour);
        internal static readonly Time CallistoanMonth = (402.08515 * Hour);
        internal static readonly Time SaturnianYear = (10759.22 * Day);
        internal static readonly Time TitanianMonth = (15.945 * Day);
        internal static readonly Time HyperianMonth = (15.945 * Day);
        internal static readonly Time UranianYear = (30688.5 * Day);
        internal static readonly Time NeptunianYear = (60182 * Day);
        internal static readonly Time PlutonicYear = (90560 * Day);

        public static StarZone Local
        {
            get
            {
                return StarZone.Local;
            }

            //internal set
            //{
            //    local = value;
            //}
        }

        
    }
}