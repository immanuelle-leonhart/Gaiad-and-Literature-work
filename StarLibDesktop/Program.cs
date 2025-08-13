using System;
using WebWindows;

namespace StarLibDesktop
{
    class Program
    {
        static void Main(string[] args)
        {
            var window = new WebWindow("My super app");
            window.NavigateToString("<h1>Hello, world!</h1> This window is from a .NET Core app.");
            window.WaitForExit();
        }
    }
}
