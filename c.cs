using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Numerics;

namespace StarCalendar
{
    internal static class c
    {
        internal static List<CultureInfo> formats = getformats();

        //StarSystems
        internal static StarSystem Amaterasu = new StarSystem("Amaterasu");

        //Planets
        internal static PlanetZone Terra = new PlanetZone("Terra", Day, Amaterasu);
        internal static PlanetZone Mars = new PlanetZone("Mars", Sol, Amaterasu);

        //Zones
        internal static Zone UTC = new Zone();

        internal static TimeSpanInfo Millisecond = new TimeSpanInfo(10000);
        internal static int TicksPerMillisecond = 10000;
        internal static TimeSpanInfo Second = Millisecond * 1000;
        internal static int TicksPerSecond = TicksPerMillisecond * 1000;
        internal static TimeSpanInfo Minute = Second * 60;
        internal static int TicksPerMinute = TicksPerSecond * 60;
        internal static TimeSpanInfo Hour = Minute * 60;
        internal static int TicksPerHour = TicksPerMinute * 60;
        internal static TimeSpanInfo Day = Hour * 24;
        internal static int TicksPerDay = TicksPerHour * 24;
        internal static TimeSpanInfo Decidi = Day / 10;
        internal static TimeSpanInfo Centidi = Day / 100;
        internal static TimeSpanInfo Millidi = Day / 1000;
        internal static TimeSpanInfo Microdi = Day / 1000000;
        internal static TimeSpanInfo Nanodi = Day / 1000000000; //Only Metric Time needed
        internal static TimeSpanInfo Sol = 1.02749125 * Day;
        internal static TimeSpanInfo week = Day * 7;
        internal static TimeSpanInfo month = week * 4;
        internal static TimeSpanInfo Year = week * 52;
        internal static TimeSpanInfo Leap = Year + week;
        internal static TimeSpanInfo DoubleLeap = Leap + week;
        internal static TimeSpanInfo Sixyear = Year * 6 + week; //6 years, 313 weeks;
        internal static TimeSpanInfo Seventy_Eight = Sixyear * 13 + week; //78 years, 4070 weeks;
        internal static TimeSpanInfo AverageYear = Day * 365.256410256;
        //internal static TimeSpanInfo SiderealYear = Day * 365.25636;
        internal static TimeSpanInfo SiderealYear = Seventy_Eight / 78;
        internal static TimeSpanInfo k = SiderealYear * 1000;
        internal static TimeSpanInfo m = k * 1000;
        internal static TimeSpanInfo b = m * 1000;
        internal static TimeSpanInfo a = 200 * m;
        internal static StarDate manu = StarDate.AbstractDate(14 * b);
        internal static StarDate maya = manu + 154 * Seventy_Eight; //10k BC + 154 * 78 = 12012
        internal static DateTime maya_net = new DateTime(2011, 12, 26); //2011-12-26
        //internal static DateTime new_year_12018 = new DateTime(2017, 12, 18, 0, 0, 0, DateTimeKind.Utc); //Sunday Saggittarius 1, 12013
        //internal static StarDate Trump1 = manu + 154 * Seventy_Eight + 6 * Year; //new_year_12018, Dec 18 2017
        //internal static StarDate y2k = manu + (12 * k);
        internal static StarDate netstart = maya - new TimeSpanInfo(maya_net.Ticks);
        internal static StarDate julian = maya - 2455921 * Day;
        internal static TimeSpanInfo tr = b * 1000;



        internal static Dictionary<string, PlanetZone> Planets = new Dictionary<string, PlanetZone>();
        internal static Dictionary<string, StarSystem> StarSystems = new Dictionary<string, StarSystem>();


        //internal static Dictionary<string, NaturalCycle> CachedCycles = new Dictionary<string, NaturalCycle>();
        internal static readonly TimeSpanInfo LunarMonth = Day * 29.53059;
        internal static readonly TimeSpanInfo MercurialYear = (87.9691 * Day);
        internal static readonly TimeSpanInfo MercurialDay = (58.646 * Day);
        internal static readonly TimeSpanInfo VenusianYear = (224.701 * Day);
        internal static readonly TimeSpanInfo VenusianSolation = (116.75 * Day);
        internal static readonly TimeSpanInfo MartianSol = (1.02749125 * Day);
        internal static readonly TimeSpanInfo MartianYear = (686.971 * Day);
        internal static readonly TimeSpanInfo PhobosMonth = (0.31891023 * Day);
        internal static readonly TimeSpanInfo DeimosMonth = (1.263 * Day);
        internal static readonly TimeSpanInfo CereanYear = (1683.14570801 * Day);
        internal static readonly TimeSpanInfo JovianYear = (4332.59 * Day);
        internal static readonly TimeSpanInfo IoanMonth = (42.47665 * Hour);
        internal static readonly TimeSpanInfo EuropanMonth = (85.29825 * Hour);
        internal static readonly TimeSpanInfo GanymedeanMonth = (171.99327 * Hour);
        internal static readonly TimeSpanInfo CallistoanMonth = (402.08515 * Hour);
        internal static readonly TimeSpanInfo SaturnianYear = (10759.22 * Day);
        internal static readonly TimeSpanInfo TitanianMonth = (15.945 * Day);
        internal static readonly TimeSpanInfo HyperianMonth = (15.945 * Day);
        internal static readonly TimeSpanInfo UranianYear = (30688.5 * Day);
        internal static readonly TimeSpanInfo NeptunianYear = (60182 * Day);
        internal static readonly TimeSpanInfo PlutonicYear = (90560 * Day);

        public static Zone Local
        {
            get
            {
                return Zone.Here;
            }

            //internal set
            //{
            //    local = value;
            //}
        }

        private static List<CultureInfo> getformats()
        {
            int counter = 0;
            string line;
            List<CultureInfo> formats = new List<CultureInfo>();
            string path = "Languages.csv";
            //int lastslash = Gedcom.LastIndexOf('/');
            //string Filename = Gedcom.Substring(lastslash + 1);
            //Gedson ged = new Gedson();
            System.IO.StreamReader file = new StreamReader(path);
            while ((line = file.ReadLine()) != null)
            {
                Console.WriteLine(line);
                CultureInfo form = new CultureInfo(line);
                formats.Add(form);
                counter++;
            }
            return formats;
        }
    }
}