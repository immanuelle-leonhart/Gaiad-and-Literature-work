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
            //CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("ja");
            //Console.WriteLine(CultureInfo.CurrentCulture.DateTimeFormat.LongDatePattern);
            Console.WriteLine(StarDate.Now.ToString());
            //StarDate.LongDate = true;
            //Console.WriteLine(StarDate.Now.ToString());
        }
    }
}
