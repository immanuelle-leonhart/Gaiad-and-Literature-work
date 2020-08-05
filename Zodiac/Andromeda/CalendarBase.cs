using Microsoft.AspNetCore.Components;
using System;
using System.Collections.Generic;
using System.Text;

namespace StarLib.Forms
{
    public class CalendarBase : ComponentBase
    {
        public EventCallback ClickDate(int i)
        {
            dt.Day = i;
            return new EventCallback();
        }
        public EventCallback SagClick(int i)
        {
            dt.Day += 28;
            dt.Day = i;
            return new EventCallback();
        }
        public EventCallback PrevMonth()
        {
            Month--;
            return new EventCallback();
        }
        public EventCallback NextMonth()
        {
            Month++;
            return new EventCallback();
        }
        public StarDate dt = StarDate.Now;
        //public int MonthDays { get; protected set; }
        public int YearMonths { get; protected set; } = 14;
        public StarDate Foundation { get; protected set; } = StarDate.Now;
        public string[] Months { get; set; } = StarLib.StarCulture.CurrentCulture.GetMonthList();
        public int Month { get; protected set; } = StarDate.Now.Month;
        public int Year { get; protected set; } = StarDate.Now.Year;
        private void Update(StarDate star)
        {
            dt = star;
            YearMonths = dt.GetYearMonths();
            Foundation = dt;
            Month = dt.Month;
            Year = dt.Year;
        }
    }
}
