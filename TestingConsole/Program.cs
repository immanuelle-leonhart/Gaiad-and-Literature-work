using StarLib
namespace TestingConsole
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, World!");
            StarDate starDate = StarDate.UtcNow();
            Console.WriteLine(StarDate.Now());
        }
    }
}
