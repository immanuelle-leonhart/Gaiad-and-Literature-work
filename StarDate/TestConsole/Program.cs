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
            try
            {
                Console.WriteLine("=== StarDate Test Console ===");
                
                // Show current Gregorian date first
                DateTime now = DateTime.Now;
                Console.WriteLine($"Current Gregorian Date: {now:yyyy-MM-dd HH:mm:ss}");
                
                // Test StarDate functionality now that we fixed the circular dependency
                Console.WriteLine("\n--- Testing StarDate.Now ---");
                StarDate starNow = StarDate.Now;
                Console.WriteLine($"StarDate.Now: {starNow}");
                
                Console.WriteLine("\n--- Testing StarDate Properties ---");
                Console.WriteLine($"Palace (宮): {starNow.Palace}");
                Console.WriteLine($"ISO Week: {starNow.WeekOfYear}");
                Console.WriteLine($"ISO Day of Week: {starNow.IsoDayOfWeek}");
                Console.WriteLine($"Month Name: {starNow.MonthName}");
                Console.WriteLine($"Day: {starNow.Day}");
                Console.WriteLine($"Year: {starNow.Year}");
                
                Console.WriteLine("\n--- Testing StarDate Conversion ---");
                StarDate converted = new StarDate(now);
                Console.WriteLine($"Converted from DateTime: {converted}");
                
                Console.WriteLine("\n--- Testing StarDate Parsing ---");
                StarDate parsed = StarDate.Parse("12020-9-9");
                Console.WriteLine($"Parsed StarDate: {parsed}");
                
                Console.WriteLine("\n✅ StarDate functionality is working!");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
            }
            
            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }


        
    }
}
