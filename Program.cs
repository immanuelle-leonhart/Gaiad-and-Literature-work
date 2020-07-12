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
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("ja");
            StarDate.LongDefault = true;
            StarDate dt = StarDate.Now.AddDays(6);
            Console.WriteLine(dt.DayOfWeek);
        }
    }
}
