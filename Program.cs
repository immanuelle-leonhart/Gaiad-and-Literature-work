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

            StarDate dt = StarDate.Now;
            //Console.WriteLine(dt.ToString("MMMM"));


            foreach (StarCulture culture in StarCulture.Cultures)
            {
                StarDate.ConsoleTest(dt, culture);
            }
        }
    }
}
