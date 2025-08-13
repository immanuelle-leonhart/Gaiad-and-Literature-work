using WebWindows.Blazor;
using System;

namespace BlazorDesktopApp
{
    public class Program
    {
        static void Main(string[] args)
        {
            ComponentsDesktop.Run<Startup>("Celestial Calendar Converter", "wwwroot/index.html");
        }
    }
}
