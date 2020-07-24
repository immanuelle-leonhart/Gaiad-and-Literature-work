using StarLib;
using System;
using System.ComponentModel.DataAnnotations;

public class Converter
{
    public DateTime dateTime { get; set; }
    public StarDate starDate { get; set; }
    public int year { get; set; }
    public int month { get; set; }
    public int day { get; set; }

    public StarDate GetStarDate()
    {
        if((this.dateTime.Year == 1) && (this.dateTime.Month == 1) && (this.dateTime.Day == 1))
        {
            return new StarDate(new DateTime(1, 1, 1));
        }
        else
        {
            return new StarDate(this.dateTime);
        }
    }
}