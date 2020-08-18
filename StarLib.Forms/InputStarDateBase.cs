using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Management.Automation;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Components.Forms;
using StarLib;

namespace StarLib.Forms
{
    public class InputStarDateBase : InputBase<StarDate>
    {
        public bool present = false;
        private string[] months;
        private long year;
        private long month;
        private long day;
        private long hour;
        private long min;
        private long sec;
        private long millisec;
        private long ticks;

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
                return (int)year;
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
                return (int)month;
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
                return (int)day;
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
                return (int)hour;
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
                return (int)min;
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
                return (int)sec;
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
                return (int)millisec;
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
                return (int)ticks;
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
        protected override bool TryParseValueFromString(string value, out StarDate result, out string validationErrorMessage)
        {
            // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
            // types here, because the underlying InputBase already covers that.
            try
            {
                result = StarDate.DataParse(value);
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
        protected override string FormatValueAsString(StarDate value)
        {
            if (value == null)
            {
                throw new ArgumentNullException();
            }
            else
            {
                return value.Data;
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
