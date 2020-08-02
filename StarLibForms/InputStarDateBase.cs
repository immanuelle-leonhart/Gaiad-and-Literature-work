using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Forms;
using StarLib;
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading.Tasks;

namespace StarLib.Forms
{
    public class InputStarDateBase : InputBase<StarDate>
    {
        private int day;
        private int month;
        private int year;
        private int monthDays;
        private int yearMonths;

        //[Parameter] public new StarLib.StarDate Value { get => sdt; set => sdt = value; }

        public int MonthDays
        {
            get
            {
                return monthDays;
            }
        }
        public int YearMonths
        {
            get
            {
                return yearMonths;
            }
        }

        public string[] Months { get; set; } = StarLib.StarCulture.CurrentCulture.GetMonthList();

        protected override void OnInitialized()
        {
            Value = StarLib.StarDate.Now;
            year = Value.Year;
            month = Value.Month;
            day = Value.Day;
            monthDays = Value.GetMonthDays();
            yearMonths = Value.GetYearMonths();
        }

        /// <inheritdoc />
        protected override bool TryParseValueFromString(string value, [MaybeNull] out StarDate result, [NotNullWhen(false)] out string validationErrorMessage)
        {
            // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
            // types here, because the underlying InputBase already covers that.
            try
            {
                result = StarDate.fromQuickString(value);
                validationErrorMessage = "Success";
                return true;
            }
            catch (Exception)
            {
                result = default;
                validationErrorMessage = "Invalid value";
                return false;
            }
        }

        /// <inheritdoc />
        protected override string FormatValueAsString([AllowNull] StarDate value)
        {
            if (value == null)
            {
                throw new ArgumentNullException();
            }
            else
            {
                return value.QuickString();
            }
        }

        public int Day
        {
            get => day; set
            {
                StarDate dt = Value;
                dt.Day = value;
                Value = dt;
                year = Value.Year;
                month = Value.Month;
                day = Value.Day;
                monthDays = Value.GetMonthDays();
                yearMonths = Value.GetYearMonths();
            }
        }
        public int Month
        {
            get => month; set
            {
                StarDate dt = Value;
                dt.Month = value;
                Value = dt;
                year = Value.Year;
                month = Value.Month;
                day = Value.Day;
                monthDays = Value.GetMonthDays();
                yearMonths = Value.GetYearMonths();
            }
        }
        public int Year
        {
            get => year; set
            {
                StarDate dt = Value;
                dt.Year = value;
                Value = dt;
                year = Value.Year;
                month = Value.Month;
                day = Value.Day;
                monthDays = Value.GetMonthDays();
                yearMonths = Value.GetYearMonths();
            }
        }
    }
}
