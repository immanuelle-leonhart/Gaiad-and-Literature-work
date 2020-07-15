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
            int i = 1;
            while ( i < 10)
            {
                Console.WriteLine(StarZone.Local.ToString(i++));
            }
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
