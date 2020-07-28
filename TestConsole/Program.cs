using StarLib;
using System;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(new StarDate(12020, 1, 13));
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
