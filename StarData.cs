//using Consul;
using System;

namespace StarCalendar
{
    internal class StarData
    {
        public static StarData UTC = new StarData("UTC");
        public static StarData Local = new StarData("Local");

        private static StarData GetStandard()
        {
            throw new NotImplementedException();
        }

        private string note;
        private TimeSpanInfo error;

        public StarData(string v)
        {
        }

        public static StarData Standard { get; internal set; }
        public static StarData Utc { get; internal set; }
    }
}