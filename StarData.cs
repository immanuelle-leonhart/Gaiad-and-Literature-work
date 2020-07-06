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
        //private bool hasTimeZone;
        //private bool complexTimeZone;
        //private bool IsTerran;

        public StarData(string v)
        {

            switch (v)
            {
                case "UTC":
                    this.timeZone = Zone.UTC;
                    break;
                case "Local":
                    this.timeZone = Zone.Local;
                    break;
                default:
                    this.timeZone = Zone.FindTimeZone(v);
                    break;
            }
            this.note = "";
            this.arraylength = 10;
            this.error = new TimeSpanInfo(0);
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

            this.note = "";
            this.timeZone = Zone.UTC;
        }

        public StarData(Zone uTC)
        {
            this.timeZone = uTC;
            this.note = "";
            this.error = new TimeSpanInfo(0);
            this.arraylength = 10;
        }

        public static StarData Standard { get; internal set; }
        public static StarData Utc { get; internal set; }
        public bool IsTerran
        {
            get
            {
                try
                {
                    return timeZone.IsTerran;
                }
                catch (NullReferenceException)
                {
                    return false;
                }
            }
        }
        public bool ComplexTimeZone
        {
            get
            {
                return timeZone.SupportsDaylightSavingTime;
            }

        }
        public bool HasTimeZone
        {
            get
            {
                return timeZone.hasTimeZone;
            }

        }
    }
}