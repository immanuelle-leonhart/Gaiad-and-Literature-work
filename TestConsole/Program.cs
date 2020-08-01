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
            StarDate dt = StarDate.Now.Date;
            Console.WriteLine(dt);
            string s = dt.QuickString();
            Console.WriteLine(s);
            Console.WriteLine(StarDate.fromQuickString(s));
        }
    }
}
