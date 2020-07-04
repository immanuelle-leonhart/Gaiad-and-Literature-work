using System;
using System.Collections.Generic;
using System.Numerics;

namespace StarCalendar
{
    public class Zone
    {
        public PlanetZone planet;
        private TimeZoneInfo terranTimeZone;
        private TimeSpanInfo extraterrestrialoffset;

        internal static Zone Here()
        {
            return new Zone(TimeZoneInfo.Local);
        }

        //private PlanetZone planet;

        //public TimeSpanInfo offset;

        //public Zone(TimeZoneInfo terranTimeZone, PlanetZone planet, TimeSpanInfo offset)
        //{
        //    this.terranTimeZone = terranTimeZone;
        //    this.planet = planet;
        //    this.offset = offset;
        //}

        //public static readonly Zone Here = new Zone(TimeZoneInfo.Local);

        public Zone(TimeZoneInfo local)
        {
            this.terranTimeZone = local;
            this.planet = c.Terra;
        }

        public Zone(PlanetZone planet)
        {
            this.planet = planet;
            if (this.Sol())
            {
                this.terranTimeZone = TimeZoneInfo.Utc;
            }
            else
            {
                this.extraterrestrialoffset = new TimeSpanInfo(0);
            }
        }

        internal static void ConvertTime(StarDate starDate, Zone z2)
        {
            throw new NotImplementedException();
        }

        

        internal bool IsDaylightSavingTime(StarDate starDate)
        {
            throw new NotImplementedException();
        }

        internal bool IsDaylightSavingTime()
        {
            throw new NotImplementedException();
        }

        internal bool SupportsDaylightSavingTime()
        {
            throw new NotImplementedException();
        }

        public Zone(PlanetZone planet, TimeSpanInfo offset)
        {
            this.planet = planet;
            if (this.Sol())
            {
                List<TimeZoneInfo> timezones = new List<TimeZoneInfo>(TimeZoneInfo.GetSystemTimeZones());
                List<TimeZoneInfo> complextimezones = new List<TimeZoneInfo>();
                List<TimeZoneInfo> matches = new List<TimeZoneInfo>();
                foreach (TimeZoneInfo timeZone in timezones)
                {
                    if (timeZone.BaseUtcOffset == offset)
                    {
                        matches.Add(timeZone);
                    }
                    else if (timeZone.SupportsDaylightSavingTime)
                    {
                        complextimezones.Add(timeZone);
                    }
                }

                if (matches.Count == 0)
                {
                    //in the future do daylight savings time related stuff
                    foreach (TimeZoneInfo zone in complextimezones)
                    {
                        //Console.WriteLine(zone);
                    }
                    TimeZoneInfo timeZone = TimeZoneInfo.CreateCustomTimeZone("custom_data timezone " + offset, new TimeSpan((long) offset.ticks), "custom_data timezone " + offset, "custom_data timezone " + offset);
                    this.terranTimeZone = timeZone;
                }
                else
                {
                    this.terranTimeZone = matches[0];
                }
            }
            else
            {
                this.extraterrestrialoffset = offset;
            }
        }

        public Zone(TimeZoneInfo local, PlanetZone planet, TimeSpanInfo offset2) : this(local)
        {
            this.planet = planet;
            throw new NotImplementedException();
        }

        public Zone(TimeSpanInfo time, PlanetZone planet)
        {
            this.planet = planet;
            if (this.Sol())
            {
                this.terranTimeZone = TimeZoneInfo.CreateCustomTimeZone("customtimezone", time.timespan(), "customtimezone", "customtimezone");
            }
            else
            {
                this.extraterrestrialoffset = time;
            }
            throw new NotImplementedException();
        }

        public Zone()
        {
            this.planet = c.Terra;
            this.terranTimeZone = TimeZoneInfo.Utc;
        }

        public TimeSpanInfo Offset()
        {
            return Offset(StarDate.Now());
        }

        public TimeSpanInfo Offset(StarDate dt)
        {
            if (this.Sol() && this.terranTimeZone.SupportsDaylightSavingTime)
            {
                try
                {
                    return new TimeSpanInfo(this.terranTimeZone.GetUtcOffset(dt.Convert()));
                }
                catch(Exception)
                {
                    return new TimeSpanInfo(this.terranTimeZone.BaseUtcOffset);
                }
            }
            else if (this.Sol())
            {
                return new TimeSpanInfo(this.terranTimeZone.BaseUtcOffset);
            }
            else
            {
                return this.extraterrestrialoffset;
            }
        }

        //private static Zone TerranZone(TimeZoneInfo timeZone)
        //{
        //    TimeSpanInfo offset = new TimeSpanInfo(timeZone.BaseUtcOffset);
        //    return new Zone(timeZone, c.Terra, offset);
        //}

        internal static Zone get()
        {
            TimeZoneInfo terranTimeZone = TimeZoneInfo.Local;
            if (d.planetstring == "Terra")
            {
                //PlanetZone planet = PlanetZone.get("Terra");
                TimeSpanInfo offset2 = (TimeSpanInfo)terranTimeZone.BaseUtcOffset;
                return new Zone(terranTimeZone, c.Terra, offset2);
            }
            else
            {
                PlanetZone planet2 = PlanetZone.get(d.planetstring);
                TimeSpanInfo offset2 = d.offset;
                return new Zone(terranTimeZone, planet2, offset2);
            }

        }

        internal StarDate Convert(StarDate input)
        {
            //Console.WriteLine("Converting");
            DateTime dt = DateTime.Now;
            if (this.Sol())
            {
                try
                {
                    dt = input.Convert();
                    TimeZoneInfo timeZone = this.terranTimeZone;
                    DateTime dt2;
                    try
                    {
                        dt2 = TimeZoneInfo.ConvertTimeFromUtc(dt, timeZone);
                    }
                    catch (ArgumentOutOfRangeException)
                    {
                        //dt2 = dt + this.Offset().timespan();
                        throw new NotImplementedException();
                    }
                    //throw new NotImplementedException();
                    return new StarDate(dt2, this);
                }
                catch (ArgumentOutOfRangeException)
                {
                    TimeSpanInfo offset = (TimeSpanInfo)this.terranTimeZone.BaseUtcOffset;
                    return input + offset;
                }
                catch (OverflowException)
                {
                    TimeSpanInfo offset = (TimeSpanInfo)this.terranTimeZone.BaseUtcOffset;
                    return input + offset;
                }
                
            }
            else
            {
                return input + this.extraterrestrialoffset;
            }
            
            
            
        }

        public override string ToString()
        {
            return this.Name();
        }

        //internal string 
        //{
        //    throw new NotImplementedException();
        //}

        public string Name()
    {
            switch (this.planet.Name)
            {
                case "Terra":
                    return this.terranTimeZone.DisplayName + " Terra";
                case "Mars":
                    double MartianOffset = (double)(this.Offset() / c.Hour);
                    string timezone;
                    if (MartianOffset > 0)
                    {
                        timezone = "MTC +" + MartianOffset + " ";
                    }
                    else
                    {
                        timezone = "MTC -" + MartianOffset + " ";
                    }
                    switch (MartianOffset)
                    {
                        case 0:
                            return timezone + "Meridiani Planum";
                        case 1:
                            return timezone + "Noachis";
                        case 2:
                            return timezone + "Arabia Terra";
                        case 3:
                            return timezone + "Huygens";
                        case 4:
                            return timezone + "West Hellas";
                        case 5:
                            return timezone + "East Hellas";
                        case 6:
                            return timezone + "Isidis";
                        case 7:
                            return timezone + "Hesperia Planum";
                        case 8:
                            return timezone + "Nepenthe";
                        case 9:
                            return timezone + "West Elysium";
                        case 10:
                            return timezone + "Central Elysium";
                        case 11:
                            return timezone + "East Elysium";
                        case 12:
                            return timezone + "Amazonis";
                        case -11:
                            return timezone + "West Cerebus";
                        case -10:
                            return timezone + "East Cerebus";
                        case -9:
                            return timezone + "Olympus Mons";
                        case -8:
                            return timezone + "Arsia";
                        case -7:
                            return timezone + "West Tharsis";
                        case -6:
                            return timezone + "East Tharsis";
                        case -5:
                            return timezone + "Upper Mariner";
                        case -4:
                            return timezone + "Lower Mariner";
                        case -3:
                            return timezone + "Argyre";
                        case -2:
                            return timezone + "New Cascadia";
                        case -1:
                            return timezone + "Oxia Palus";
                        default:
                            return timezone;
                    }
                default:
                    string name = this.planet.Name;
                    int offset = (int) (this.Offset() / c.Hour);
                    string offsetstring;
                    if (offset < 0)
                    {
                        offsetstring = "" + offset;
                    }
                    else
                    {
                        offsetstring = "+" + offset;
                    }

                    string delay = "";

                    if (this.Sol() == false)
                    {
                        throw new NotImplementedException();
                        //delay = " " + this.planet.Sun.distance_at_time(now).ToString();
                    }

                    return name + " " + offsetstring + delay;
            }
        }

        internal static Zone Parse(string prim)
        {
            //GMT-8
            if ((prim.Substring(0, 3) == "GMT") || (prim.Substring(0, 3) == "UTC"))
            {
                int hours = int.Parse(prim.Substring(3));
                TimeSpanInfo time = hours * c.Hour;
                return new Zone(time, c.Terra);
            }
            else if(prim.Substring(0, 3) == "MTC")
            {
                int hours = int.Parse(prim.Substring(3));
                TimeSpanInfo time = hours * c.Hour;
                return new Zone(time, c.Mars);
                throw new NotImplementedException();
            }
            else
            {
                Console.WriteLine(prim);
                Console.WriteLine(prim.Substring(0, 3));
                throw new NotImplementedException();
            }
        }

        internal bool Sol()
        {
            //Console.WriteLine(this.planet.Sun.name);
            return this.planet.Sun.name == "Amaterasu";
            //return this.planet.Names == "Amaterasu";
        }

        internal TimeSpanInfo LocalDay()
        {
            return this.planet.LocalDay;
        }

        public static bool operator ==(Zone z1, Zone z2)
        {
            throw new NotImplementedException();
        }

        public static bool operator !=(Zone z1, Zone z2)
        {
            throw new NotImplementedException();
        }

        public static bool operator ==(Zone z, TimeZoneInfo t)
        {
            return z.terranTimeZone == t;
        }

        public static bool operator !=(Zone z, TimeZoneInfo t)
        {
            return z.terranTimeZone != t;
        }

        public static bool operator ==(TimeZoneInfo t, Zone z)
        {
            return z == t;
        }

        public static bool operator !=(TimeZoneInfo t, Zone z)
        {
            return z != t;
        }

        public override bool Equals(object obj)
        {
            if (ReferenceEquals(this, obj))
            {
                return true;
            }

            if (ReferenceEquals(obj, null))
            {
                return false;
            }

            throw new NotImplementedException();
        }

        public override int GetHashCode()
        {
            throw new NotImplementedException();
        }
    }
}