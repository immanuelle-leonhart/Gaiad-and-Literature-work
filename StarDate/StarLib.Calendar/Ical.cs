using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace StarLib.Calendar
{
    public class Ical
    {
        public static string PRODID { get; private set; }

        public static void WriteDay(StreamWriter stream, StarDate dt)
        {
            dt = dt.Date;
            stream.WriteLine("BEGIN:VEVENT");
            stream.WriteLine("DTSTART;VALUE=DATE:" + dt.RFC1123);
            stream.WriteLine("DTEND;VALUE=DATE:" + dt.AddDays(1).RFC1123);
            stream.WriteLine("DTSTAMP;VALUE=DATE:" + DTSTAMP(dt));
            stream.WriteLine("UID;VALUE=DATE:" + GetUID(dt));
            stream.WriteLine("CREATED:" + StarDate.Now.RFC1123);
            stream.WriteLine("DESCRIPTION:" + GetDescription(dt));
            stream.WriteLine("LAST-MODIFIED:" + dt.RFC1123);
            stream.WriteLine("LOCATION:Terra");
            stream.WriteLine("SEQUENCE:0");
            stream.WriteLine("STATUS:CONFIRMED");
            stream.WriteLine("SUMMARY:" + dt.ToLongString());
            stream.WriteLine("TRANSP:TRANSPARENT");
            stream.WriteLine("END:VEVENT");
        }

        private static string DTSTAMP(StarDate dt)
        {
            return dt.RFC1123;
        }

        private static string GetDescription(StarDate dt)
        {
            return dt.ToLongString();
        }

        private static string GetUID(StarDate dt)
        {
            return dt + "@order.life";
        }

        public static void WriteYear(StreamWriter stream, int year)
        {
            //start boilerplate
            stream.WriteLine("BEGIN:VCALENDAR");
            stream.WriteLine("METHOD:PUBLISH");
            stream.WriteLine("PRODID:" + PRODID);
            stream.WriteLine("VERSION:2.0");
            //write days
            StarDate StarYearBeginning = new StarDate(year, 1, 1);
            StarDate StarYearEnd = new StarDate(year + 1, 1, 1).AddDays(-1);
            StarDate GregYearBeginning = new DateTime(year, 1, 1);
            StarDate GregYearEnd = new DateTime(year, 12, 31);
            StarDate Beginning;
            if (GregYearBeginning < StarYearBeginning)
            {
                Beginning = GregYearBeginning;
            }
            else
            {
                Beginning = StarYearBeginning;
            }


            StarDate End;
            if (GregYearEnd > StarYearEnd)
            {
                End = GregYearEnd;
            }
            else
            {
                End = StarYearEnd;
            }

            StarDate dt = Beginning;
            while (dt <= End)
            {
                WriteDay(stream, dt++);
            }
            //end boilerplate
            stream.WriteLine("END:VCALENDAR");
        }
    }
}
