using System;

namespace StarCalendar
{
    public class PlanetZone
    {
        internal string Name = "Default Planet Name";
        internal TimeSpanInfo LocalDay = c.Day;
        internal StarSystem Sun = StarSystem.Amaterasu;
        public static PlanetZone Terra = new PlanetZone("Terra", c.Day, StarSystem.Amaterasu);
        public static PlanetZone Mars = new PlanetZone("Mars", c.Sol, StarSystem.Amaterasu);

        public PlanetZone(string Name, TimeSpanInfo LocalDay, StarSystem Sun)
        {
            this.Name = Name;
            this.LocalDay = LocalDay;
            this.Sun = Sun;
        }

        public bool Sol
        {
            get
            {
                return this.Sun.Sol;
            }
        }

        internal static PlanetZone get(string v)
        {
            throw new NotImplementedException();
        }
    }
}