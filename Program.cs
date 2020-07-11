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
            Console.WriteLine(StarDate.Now.ToString());
            Console.WriteLine(StarDate.Now);
            
            //System.Threading.Thread.CurrentThread.CurrentUICulture = new CultureInfo("ja-JP");
            //Console.WriteLine(DateTime.Now);


            //foreach (StarCulture culture in StarCulture.Cultures)
            //{
            //    StarDate.ConsoleTest(StarDate.Now, culture);
            //}
        }
    }
}
