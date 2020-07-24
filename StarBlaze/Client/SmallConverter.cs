using StarLib;
using System;
using System.ComponentModel.DataAnnotations;

public class SmallConverter
{
    private DateTime dateTime;

    public DateTime DateTime
    {
        get => dateTime;  set
        {
            dateTime = value;
            starDate = (StarDate)dateTime;
        }
    }
    public StarDate starDate;

    public int Year
    {
        get => starDate.Year; set
        {
            starDate.Year = value;
            dateTime = starDate.DateTime;
        }
    }
    public int Month
    {
        get => starDate.Month; set
        {
            starDate.Month = value;
            dateTime = starDate.DateTime;
        }
    }
    public int Day
    {
        get => starDate.Day; set
        {
            starDate.Day = value;
            dateTime = starDate.DateTime;
        }
    }

    public StarDate GetStarDate()
    {
        if ((this.DateTime.Year == 1) && (this.DateTime.Month == 1) && (this.DateTime.Day == 1))
        {
            return new StarDate(new DateTime(1, 1, 1));
        }
        else
        {
            return new StarDate(this.DateTime);
        }
    }
}