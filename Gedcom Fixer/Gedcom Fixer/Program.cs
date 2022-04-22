// See https://aka.ms/new-console-template for more information
Console.WriteLine("Hello, World!");

GedcomFixer f = new GedcomFixer();

f.fix(@"../../../../../Gaiad.ged");

f.idToGiven(@"../../../../../Gaiad.ged");