using System;
using System.Text;

namespace StarLib.Calendar
{
    public class Ical
    {

        public static void WriteIcal()
        {
            WriteIcal("");
        }

        public static void WriteIcal(string v)
        {
            WriteIcal(v, DateTime.Now.Year);
        }

        public static void WriteIcal(string v1, int v2)
        {
            WriteIcal(v1, v2, v2);
        }

        public static void WriteIcal(string path, int v2, int v3)
        {
            string[] p = path.Split('/');
            string filename = p[p.Length - 1];
            int i = 0;
            StringBuilder stringBuilder = new StringBuilder();
            while (i < p.Length - 1)
            {
                stringBuilder.Append(p[i]);
                stringBuilder.Append('/');
            }
            path = stringBuilder.ToString();
            if (filename.Length == 0)
            {
                if (v2 == v3)
                {
                    filename = "StarCalendar_of_" + v2 + ".ics";
                }
                else
                {
                    filename = "StarCalendar_of_" + v2 + "_to_" + v3 + ".ics";
                }
            }
            else if (!filename.EndsWith(".ics"))
            {
                filename += ".ics";
            }

            //Path filepath = $"{path}{filename}";

            //StreamWriter ical = new StreamWriter(path + filename);
        }
    }
}
