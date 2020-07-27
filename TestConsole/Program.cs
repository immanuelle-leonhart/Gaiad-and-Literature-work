using StarLib;
using System;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(StarDate.UtcNow.Julian);
            StarDate dt = StarDate.FromGreg(9999, 1, 1);
            bool b = true;
            while (b)
            {
                Console.Write(dt.GregYear);
                Console.Write("-");
                Console.Write(dt.GregMonth);
                Console.Write("-");
                Console.Write(dt.GregDay);
                Console.WriteLine();
                dt++;
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
