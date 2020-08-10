using StarLib;
//using StarLibRazor;
using System;
using System.Collections.Generic;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            //Console.WriteLine(TimeZoneInfo.Local.DisplayName);
            DateTime dt = DateTime.Now;
            DateTime.DaysInMonth(18, 3);
            _ = DateTime.Now;
            _ = DateTime.UtcNow;
            _ = StarDate.Now;
        }
    }
}
