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
            Console.WriteLine(TimeZoneInfo.Local.DisplayName);
            StarDate dt = StarDate.Now.Date;
            Console.WriteLine(dt);
            dt = new StarDate(dt.GetDatePart());
        }
    }
}
