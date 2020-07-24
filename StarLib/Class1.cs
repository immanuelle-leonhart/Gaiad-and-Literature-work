using System;
using System.IO;
using System.Reflection;

namespace StarLib
{
    public class Class1
    {
        //private static bool path;

        public static string FilePath
        {
            get
            {
                string assemblyFolder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
                string csvFileName = Path.Combine(assemblyFolder, "Languages.csv");
                return csvFileName;
            }
        }
    }
}
