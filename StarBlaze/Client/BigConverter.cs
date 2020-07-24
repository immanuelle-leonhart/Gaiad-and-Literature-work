using StarLib;
using System;
using System.ComponentModel.DataAnnotations;

public class BigConverter
{
    public int GregYear
    {
        get => starDate.GregYear; set
        {
            starDate.GregYear = value;
        }
    }
    public int GregMonth
    {
        get => starDate.Month; set
        {
            starDate.GregMonth = value;
        }
    }
    public int GregDay
    {
        get => starDate.GregDay; set
        {
            starDate.GregDay = value;
        }
    }


    public StarDate starDate;

    public int StarYear
    {
        get => starDate.Year; set
        {
            starDate.Year = value;
        }
    }
    public int StarMonth
    {
        get => starDate.Month; set
        {
            starDate.Month = value;
        }
    }
    public int StarDay
    {
        get => starDate.Day; set
        {
            starDate.Day = value;
        }
    }
}