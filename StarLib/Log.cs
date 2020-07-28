using System;
using System.IO;

namespace StarLib
{
    internal class Log
    {
        private static StreamWriter Sr = new StreamWriter("log.txt");
        internal static void WriteLine(string text)
        {
            Sr.WriteLine(text);
            Sr.Flush();
        }
    }
}