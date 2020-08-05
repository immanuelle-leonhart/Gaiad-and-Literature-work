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
            StarDate dt = StarDate.Now;
            int i = 0;
            while (i < 500)
            {
                Console.WriteLine(dt.ToLongString());
                dt.Year += 1;
                i++;
            }
        }
    }
}
