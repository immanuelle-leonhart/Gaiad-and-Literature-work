using StarLib;
using StarLibRazor;
using System;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello World!");
            Console.Write(StarDate.Now);
            Console.WriteLine(CalendarBase.test);
        }
    }
}
