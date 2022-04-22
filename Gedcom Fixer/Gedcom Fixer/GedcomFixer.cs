// See https://aka.ms/new-console-template for more information
internal class GedcomFixer
{
    private List<string> data;

    public GedcomFixer()
    {
        this.data = new List<string>();
    }

    internal void fix(string v)
    {
        try
        {
            // Create an instance of StreamReader to read from a file.
            // The using statement also closes the StreamReader.
            using (StreamReader sr = new StreamReader(v))
            {
                string line;
                // Read and display lines from the file until the end of
                // the file is reached.
                while ((line = sr.ReadLine()) != null)
                {
                    Console.WriteLine(line);
                    this.data.Add(fixLine(line));
                }
            }

            WriteFile(v);
        }
        catch (Exception e)
        {
            // Let the user know what went wrong.
            Console.WriteLine("The file could not be read:");
            Console.WriteLine(e.Message);
        }
    }

    internal void idToGiven(string v)
    {
        try
        {
            // Create an instance of StreamReader to read from a file.
            // The using statement also closes the StreamReader.
            this.data = new List<string>();
            string id = "";
            using (StreamReader sr = new StreamReader(v))
            {
                string line;
                // Read and display lines from the file until the end of
                // the file is reached.
                while ((line = sr.ReadLine()) != null)
                {
                    
                    Console.WriteLine(line);
                    if (line.StartsWith("0 @") && line.EndsWith("@ INDI"))
                    {
                        id = line.Split("@")[1];
                    }
                    if (line.StartsWith("1 NAME /"))
                    {
                        line = line.Replace("1 NAME /", "1 NAME " + id.Replace("_", " ") + " /");
                    }
                    this.data.Add(line);
                    //this.data.Add(fixLine(line));
                }
            }

            WriteFile(v);
        }
        catch (Exception e)
        {
            // Let the user know what went wrong.
            Console.WriteLine("The file could not be read:");
            Console.WriteLine(e.Message);
        }
    }

    private void WriteFile(string v)
    {
        File.Delete(v);
        using (StreamWriter sw = new StreamWriter(v))
        {
            foreach (string line in this.data)
            {
                sw.WriteLine(line);
            }
            sw.Flush();
        }
    }

    private string fixLine(string line)
    {
        if (!line.Contains('@'))
        {
            return line;
        }
        string[] vs = line.Split('@');
        int i = 0;
        string s = "";
        while (i < vs.Length)
        {
            if (i % 2 == 0)
            {
                s += vs[i];
            }
            else
            {
                s += fixId(vs[i]);
            }
            i++;
        }
        return s;
    }

    private string fixId(string v)
    {
        v = v.Trim();
        v = v.Replace(' ', '_');
        return "@" + v + "@";
    }
}