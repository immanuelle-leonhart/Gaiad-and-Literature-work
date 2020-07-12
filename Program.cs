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
            int i = 0;
            StarDate dt = StarDate.Maya;
            //Console.WriteLine(dt);
            dt -= 378 * StarDate.DayTime;
            Console.WriteLine(dt);
            while (i < 378)
            {
                Console.WriteLine(dt);
                StarDate.LongDefault = true;
                Console.WriteLine(dt);
                StarDate.LongDefault = false;
                dt++;
                i++;
            }
        }
    }
}
