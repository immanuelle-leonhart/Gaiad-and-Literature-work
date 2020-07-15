using CosmicCalendar;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Numerics;
using System.Runtime.Serialization;
using System.Security.Cryptography.X509Certificates;

namespace ConsoleApp
{
    class Program
    {
        //private static object Integers;

        static void Main(string[] args)
        {
            StarDate.MakeChart();
            print(new StarDate(10200));
        }

        public static void print(object v)
        {
            Console.WriteLine(v);
        }

        public static void print(object[] vs)
        {
            try
            {
                foreach (var entry in vs)
                {
                    Console.WriteLine(entry);
                }
            }
            catch (NullReferenceException)
            {
                int i = 0;
                while (i < vs.Length)
                {
                    Console.WriteLine(vs[i++]);
                }
            }
        }
    }
}
