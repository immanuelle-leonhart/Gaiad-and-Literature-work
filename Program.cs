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
            Console.WriteLine(StarDate.DefaultFormat);
            Console.WriteLine(StarDate.UtcNow.ToString());
        }
    }
}
