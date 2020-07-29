using StarLib;
using System;
using System.Globalization;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            Console.WriteLine(new StarDate(12020, 1, 13));
            print(StarCulture.CurrentCulture.GetMonthList());
            foreach (CultureInfo culture in CultureInfo.GetCultures(CultureTypes.AllCultures))
            {
                Console.Write(culture.TwoLetterISOLanguageName + " ");
                Console.Write(culture.Name + " ");
                Console.Write(culture.DisplayName);
                Console.WriteLine();
            }
        }

        private static void print(string[] vs)
        {
            foreach (string entry in vs)
            {
                Console.WriteLine(entry);
            }
        }
    }
}
