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

        [Parameter] public new StarLib.StarDate Value { get => sdt; set => sdt = value; }
        
        public int MonthDays
        {
            get
            {
                if (Month == 14)
                {
                    return sdt.HorusLength();
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
                if (sdt.isleapyear())
                {
                    return 14;
                }
                else
                {
                    return 13;
                }
            }
        }
        public StarLib.StarDate sdt;

        public string[] Months { get; set; } = StarLib.StarCulture.CurrentCulture.GetMonthList();

        protected override void OnInitialized()
        {
            sdt = StarLib.StarDate.Now;
        }

        /// <inheritdoc />
        protected override bool TryParseValueFromString(string? value, [MaybeNull] out StarDate result, [NotNullWhen(false)] out string? validationErrorMessage)
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
    }
}
