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

            string path = "C:/Users/SiliconProphet/Documents/GitHub/Order/StarDate/ICAL/calendar.ical";
            string path2 = "C:/Users/SiliconProphet/Documents/GitHub/Order/StarDate/ICAL/";
            string[] p = path.Split('/');
            string[] p2 = path2.Split('/');
            foreach (string entry in p2)
            {
                Console.WriteLine("line: " + entry + " length " + entry.Length);
            }
            foreach (string entry in p)
            {
                Console.WriteLine("line: " + entry);
            }
            StarDate.WriteIcal("C:/Users/SiliconProphet/Documents/GitHub/Order/StarDate/ICAL");
            StarDate.WriteIcal("C:/Users/SiliconProphet/Documents/GitHub/Order/StarDate/ICAL", 2020);
            StarDate.WriteIcal("C:/Users/SiliconProphet/Documents/GitHub/Order/StarDate/ICAL", 2010, 2020);
        }
    }
}
