using StarLib;
using System;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            StarDate dt = StarDate.Now;
            Console.WriteLine(dt.ToLongDateString());
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
