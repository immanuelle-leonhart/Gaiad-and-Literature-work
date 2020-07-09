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
            StarDate.PrintAllFormats(StarDate.Now);
            //StarDate.FullTest();
        }
    }
}
