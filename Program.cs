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
            CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("en");
            StarDate.LongDefault = true;
            StarDate dt = StarDate.Maya;
            dt -= 380 * StarDate.DayTime;
            int i = 0;
            while (i < 2000)
            {
                Console.WriteLine(dt++);
                i++;
            }
        }
    }
}
