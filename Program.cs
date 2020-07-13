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
            foreach (StarCulture culture in StarCulture.Cultures)
            {
                StarCulture.CurrentCulture = culture;
                Console.WriteLine(StarCulture.CurrentCulture.CultureName);
                StarDate.LongDefault = true;
                StarDate dt = StarDate.Maya;
                int i = 0;
                while (i < 380)
                {
                    Console.WriteLine(dt++);
                    i++;
                }
            }
        }
    }
}
