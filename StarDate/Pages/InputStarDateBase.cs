using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Forms;
using StarLib;
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading.Tasks;

namespace StarBlaze.Pages
{
    public class InputStarDateBase : InputBase<StarDate>
    {
        private int day;
        private int month;
        private int year;

        //[Parameter] public new StarLib.StarDate Value { get => sdt; set => sdt = value; }

        public int MonthDays
        {
            get
            {
                if (Value.Month == 14)
                {
                    return Value.HorusLength();
                }
                else
                {
                    return 28;
                }
            }
        }
        public int YearMonths
        {
            get
            {
                if (Value.isleapyear())
                {
                    return 14;
                }
                else
                {
                    return 13;
                }
            }
        }

        public string[] Months { get; set; } = StarLib.StarCulture.CurrentCulture.GetMonthList();

        protected override void OnInitialized()
        {
            Value = StarLib.StarDate.Now;
            year = Value.Year;
            month = Value.Month;
            day = Value.Day;
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
            }
        }
    }
}
