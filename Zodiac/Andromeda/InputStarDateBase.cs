using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Components.Forms;
using StarLib;

namespace Zodiac.Andromeda
{
    public class InputStarDateBase : InputBase<StarDate>
    {
        public bool present = false;
        private string[] months;
        private int year;
        private int month;
        private int day;
        private int hour;
        private int min;
        private int sec;
        private int millisec;
        private int ticks;

        public int MonthDays { get; protected set; }
        public int YearMonths { get; protected set; }
        public int BaseYear { get; protected set; } = StarDate.Now.Year;

        public string[] Months
        {
            get
            {
                if (months == null)
                {
                    months = StarLib.StarCulture.CurrentCulture.GetMonthList();
                }
                return months;
            }
        }

        public int Year
        {
            get
            {
                return year;
            }
            set
            {
                StarDate dt = Value;
                dt.Year = value;
                Update(dt);
            }
        }

        public int Month
        {
            get
            {
                return month;
            }
            set
            {
                StarDate dt = Value;
                dt.Month = value;
                Update(dt);
            }
        }
        public int Day
        {
            get
            {
                return day;
            }
            set
            {
                StarDate dt = Value;
                dt.Day = value;
                Update(dt);
            }
        }

        public int Hour
        {
            get
            {
                return hour;
            }
            set
            {
                StarDate dt = Value;
                dt.Hour = value;
                Update(dt);
            }
        }

        public int Min
        {
            get
            {
                return min;
            }
            set
            {
                StarDate dt = Value;
                dt.Minute = value;
                Update(dt);
            }
        }


        

        public int Sec
        {
            get
            {
                return sec;
            }
            set
            {
                StarDate dt = Value;
                dt.Second = value;
                Update(dt);
            }
        }

        public int Mil
        {
            get
            {
                return millisec;
            }
            set
            {
                StarDate dt = Value;
                dt.Millisecond = value;
                Update(dt);
            }
        }



        public int Ticks
        {
            get
            {
                return ticks;
            }
            set
            {
                StarDate dt = Value;
                dt.ExtraTicks = value;
                Update(dt);
            }
        }









        protected override void OnInitialized()
        {
            if (Value == null)
            {
                Update(StarDate.Now);
            }
            else
            {
                Update();
            }
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

        private void Update(StarDate dt)
        {
            Value = dt;
            Update();
        }

        private void Update()
        {
            Value.GetDatePart(out year, out month, out day, out hour, out min, out sec, out millisec, out ticks);
            MonthDays = Value.GetMonthDays();
            YearMonths = Value.GetYearMonths();
        }

    }
}
