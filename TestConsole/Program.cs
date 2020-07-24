using StarLib;
using System;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(StarDate.UtcNow.Julian);
            int DaysPer400Years = 146097;
            StarDate dt = StarDate.UtcNow;
            dt = dt.AddYears(-2000);
            int i = DaysPer400Years + 1;
            while (dt.Julian > 0)
            {
                Console.WriteLine(dt.GregYear + "-" + dt.GregMonth + "-" + dt.GregDay + " " + dt.GregDayOfYear + " j = " + dt.Julian); //dt.GregMonth + "-" +
                dt--;
                i--;
            }
        }

        private static int Modul(int i, int v)
        {
            if (i > 0)
            {
                return i % v;
            }
            int t = i / v;
            t--;
            return Modul(i - t * v, v);
        }
    }
}
