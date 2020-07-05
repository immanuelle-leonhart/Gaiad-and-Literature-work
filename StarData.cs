//using Consul;
using System;

namespace StarCalendar
{
    internal struct StarData
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
            switch (v)
            {
                case "UTC":
                    this.timeZone = c.UTC;
                    break;
                case "Local":
                    this.timeZone = Zone.Here;
                    break;
                default:
                    break;
            }
        }

        public StarData(int arraylength)
        {
            this.arraylength = arraylength;
            switch (arraylength)
            {
                case 1:
                    this.error = c.Year;
                    break;
                case 2:
                    this.error = c.month;
                    break;
                case 3:
                    this.error = c.Day;
                    break;
                case 4:
                    this.error = c.Hour;
                    break;
                case 5:
                    this.error = c.Minute;
                    break;
                case 6:
                    this.error = c.Second;
                    break;
                case 7:
                    this.error = c.Millisecond;
                    break;
                case 8:
                default:
                    this.error = new TimeSpanInfo(0);
                    break;
            }

            //assign timezones

            //this.timeZone = c.UTC;

            //assign notes

            //this.Note = "";

            //assign unified metadata
        }

        public StarData(Zone uTC)
        {
            this.timeZone = uTC;
        }

        public static StarData Standard { get; internal set; }
        public static StarData Utc { get; internal set; }
    }
}