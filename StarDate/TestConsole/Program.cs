using Newtonsoft.Json;
using StarLib;
//using StarLibRazor;
using System;
using System.Collections.Generic;
using System.Dynamic;
using System.Numerics;

namespace TestConsole
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== Current Date Display ===");
            
            // Show current Gregorian date
            DateTime now = DateTime.Now;
            Console.WriteLine($"Current Date and Time: {now:yyyy-MM-dd HH:mm:ss}");
            Console.WriteLine($"Current Date (Short): {now:yyyy-MM-dd}");
            Console.WriteLine($"Current Time (Short): {now:HH:mm:ss}");
            Console.WriteLine($"Day of Week: {now.DayOfWeek}");
            Console.WriteLine($"Day of Year: {now.DayOfYear}");
            
            // Calculate ISO week information manually
            var culture = System.Globalization.CultureInfo.CurrentCulture;
            var calendar = culture.Calendar;
            var dateTimeFormat = culture.DateTimeFormat;
            int isoWeek = calendar.GetWeekOfYear(now, dateTimeFormat.CalendarWeekRule, dateTimeFormat.FirstDayOfWeek);
            Console.WriteLine($"ISO Week Number: {isoWeek}");
            
            // Show UTC time as well
            DateTime utcNow = DateTime.UtcNow;
            Console.WriteLine($"UTC Time: {utcNow:yyyy-MM-dd HH:mm:ss}");
            
            Console.WriteLine();
            Console.WriteLine("Note: StarDate functionality has a circular dependency bug");
            Console.WriteLine("that causes stack overflow when trying to access current dates.");
            Console.WriteLine("This needs to be fixed in the StarLib library.");
            
            Console.WriteLine();
            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();
        }


        
    }
}
