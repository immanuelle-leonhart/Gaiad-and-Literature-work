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

        public string note;
        public TimeSpanInfo error;
        private int arraylength;
        internal Zone timeZone;

        public StarData(string v)
        {
        }

        public StarData(int arraylength)
        {
            this.arraylength = arraylength;
        }

        public StarData(Zone uTC)
        {
            this.timeZone = uTC;
        }

        public static StarData Standard { get; internal set; }
        public static StarData Utc { get; internal set; }
    }
}