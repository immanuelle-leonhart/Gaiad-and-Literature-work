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
            StarDate myStruct = new StarDate(10, 10, 10, 10);

            BigInteger big = 100000;

            StarDate star = new StarDate(big, 0, StarZone.UTC);

            var serializedMyStruct = JsonConvert.SerializeObject(myStruct);

            Console.WriteLine("JSON: " + serializedMyStruct);

            var newlyDeserializedMyStruct = JsonConvert.DeserializeObject<StarDate>(serializedMyStruct);

            Console.WriteLine("Standard deserialization result: " + newlyDeserializedMyStruct);

            dynamic dynamicDeSerializedMyStruct = JsonConvert.DeserializeObject<ExpandoObject>(serializedMyStruct);

            Console.WriteLine("Dynamic deserialization result: " + dynamicDeSerializedMyStruct);
        }
    }
}
