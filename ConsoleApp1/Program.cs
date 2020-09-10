using System;
using Kinship;
using StarLib;

namespace ConsoleApp1
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(StarDate.Now);
            Console.WriteLine(Relative.GetRelationship("F"));
        }
    }
}
