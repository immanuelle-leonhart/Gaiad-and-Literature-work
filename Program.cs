using StarCalendar;
using System;
using System.Collections.Generic;
using System.Security.Cryptography.X509Certificates;

namespace StarCalendar
{
    class Program
    {
        //private static object Integers;

        static void Main(string[] args)
        {
            
            //int i = 0;
            //while (i < 100000)
            //{
            //    Console.WriteLine(StarDate.Now.ToString("yyyyy/MM/dd hh:mm:ss tt FFFFFFF"));
            //    i++;
            //}

            StarDate dt = StarDate.Now;
            foreach (StarCulture culture in StarCulture.Cultures)
            {
                StarDate.ConsoleTest(dt, culture);
            }
        }
    }
}
