using StarCalendar;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Security.Cryptography.X509Certificates;

namespace StarCalendar
{
    class Program
    {
        //private static object Integers;

        static void Main(string[] args)
        {
            StarDate dt = StarDate.Now;
            Console.WriteLine("DDDD MMMMM ddd yyyyy");
            Console.WriteLine(StarDateFormat.FormatCustomized(dt, "DDDD MMMMM ddd yyyyy", StarCulture.InvariantCulture, new Time(0)));
            Console.WriteLine(dt.ToShortDateString());
            Console.WriteLine(dt.ToLongTimeString());
            Console.WriteLine(dt.ToShortTimeString());
        }
    }
}
