using System;

namespace StarCalendar
{
    public class PlanetZone
    {
        internal string Name;
        internal TimeSpanInfo LocalDay;
        internal StarSystem Sun;

        public PlanetZone(string Name, TimeSpanInfo LocalDay, StarSystem Sun)
        {
            this.Name = Name;
            this.LocalDay = LocalDay;
            this.Sun = Sun;
        }

        internal static PlanetZone get(string v)
        {
            throw new NotImplementedException();
        }
    }
}