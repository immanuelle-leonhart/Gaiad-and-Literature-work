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
            long b = 14 * (long)Math.Pow(10, 9);
            Console.WriteLine(b);
            
            StarDate dt = new StarDate(StarDate.TicksPerBillion * 2, StarZone.UTC);
            //Console.WriteLine(dt.Ticks);
            //Console.WriteLine(dt.FullYear);
            int i = 140; 
            while (i < 150)
            {
                StarDate sd = dt.AddTicks(StarDate.TicksPerMillion * i);
                Console.WriteLine(sd.Ticks);
                Console.WriteLine(sd.FullYear);
                Console.WriteLine("million = " + i);
                i++;
            }
        }

        public static void test(StarDate myStruct)
        {
            var serializedMyStruct = JsonConvert.SerializeObject(myStruct);

            Console.WriteLine("JSON: " + serializedMyStruct);

            var newlyDeserializedMyStruct = JsonConvert.DeserializeObject<StarDate>(serializedMyStruct);

            Console.WriteLine("Standard deserialization result: " + newlyDeserializedMyStruct);

            dynamic dynamicDeSerializedMyStruct = JsonConvert.DeserializeObject<ExpandoObject>(serializedMyStruct);

            Console.WriteLine("Dynamic deserialization result: " + dynamicDeSerializedMyStruct);
        }
    }
}
