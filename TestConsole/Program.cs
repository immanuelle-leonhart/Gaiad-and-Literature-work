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
            StarDate dt = StarDate.Now;
            Console.WriteLine(dt.DateTime);
            Console.WriteLine(dt);
            Console.WriteLine(DateTimeOffset.Now);
            Console.WriteLine(DateTimeOffset.Now);
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
