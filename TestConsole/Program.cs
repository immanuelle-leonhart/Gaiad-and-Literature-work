using StarLib;
using System;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello World!");
            Console.WriteLine(StarLib.Class1.FilePath);
            Console.WriteLine(StarDate.Now);
            Console.WriteLine(StarDate.Now.ToLongDateString());
        }
    }
}
