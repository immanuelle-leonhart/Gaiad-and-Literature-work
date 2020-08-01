// Copyright (c) .NET Foundation. All rights reserved.
// Licensed under the Apache License, Version 2.0. See License.txt in the project root for license information .

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq.Expressions;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Forms;
using Microsoft.AspNetCore.Components.Rendering;
using StarLib;

namespace StarBlaze
{
    /// <summary>
    /// An input component for editing date values.
    /// Supported types are <see cref="StarDate"/> and <see cref="StarDateOffset"/>.
    /// </summary>
    public class Oldinput<TValue> : InputBase<TValue>
    {
        private const string DateFormat = "yyyy-MM-dd"; // Compatible with HTML date inputs
        protected StarDate dt = StarDate.Now;

        //private TValue /*value*/ = default;

        /// <summary>
        /// Gets or sets the error message used when displaying an a parsing error.
        /// </summary>
        [Parameter] public string ParsingErrorMessage { get; set; } = "The {0} field must be a date.";

        ///// <inheritdoc />
        //protected override bool TryParseValueFromString(string? value, [MaybeNull] out TValue result, [NotNullWhen(false)] out string? validationErrorMessage)
        //{
        //    if (value is null)
        //    {
        //        throw new ArgumentNullException(nameof(value));
        //    }
        //    // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
        //    // types here, because the underlying InputBase already covers that.
        //    var targetType = Nullable.GetUnderlyingType(typeof(TValue)) ?? typeof(TValue);

        //    bool success;
        //    if (targetType == typeof(StarDate))
        //    {
        //        //success = TryParseStarDate(value, out result);
        //        success = true;
        //        result = (TValue)(object)dt;
        //    }
        //    else if (targetType == typeof(DateTime))
        //    {
        //        //success = TryParseStarDate(value, out result);
        //        success = true;
        //        result = (TValue)(object)(DateTime)dt;
        //    }
        //    else
        //    {
        //        throw new InvalidOperationException($"The type '{targetType}' is not a supported date type.");
        //    }

        //    if (success)
        //    {
        //        validationErrorMessage = null;
        //        return true;
        //    }
        //    else
        //    {
        //        validationErrorMessage = string.Format(ParsingErrorMessage, DisplayName ?? FieldIdentifier.FieldName);
        //        return false;
        //    }
        //}

        /// <inheritdoc />
        protected override bool TryParseValueFromString(string? value, [MaybeNull] out TValue result, [NotNullWhen(false)] out string? validationErrorMessage)
        {
            // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
            // types here, because the underlying InputBase already covers that.
            var targetType = Nullable.GetUnderlyingType(typeof(TValue)) ?? typeof(TValue);

            bool success;
            if (targetType == typeof(DateTime))
            {
                success = TryParseDateTime(value, out result);
            }
            else if (targetType == typeof(StarDate))
            {
                success = TryParseStarDate(value, out result);
            }
            else
            {
                throw new InvalidOperationException($"The type '{targetType}' is not a supported date type.");
            }

            if (success)
            {
                validationErrorMessage = null;
                return true;
            }
            else
            {
                validationErrorMessage = string.Format(ParsingErrorMessage, DisplayName ?? FieldIdentifier.FieldName);
                return false;
            }
        }

        private bool TryParseStarDate(string value, out TValue result)
        {
            bool b;
            StarDate s;
            b = StarDate.TryParse(value, DateFormat, out s);
            result = (TValue)(object)s;
            return b;
        }

        private bool TryParseDateTime(string value, out TValue result)
        {
            bool b;
            StarDate s;
            b = StarDate.TryParse(value, DateFormat, out s);
            result = (TValue)(object)(DateTime)s;
            return b;
        }

        private static List<int> month28;
        private static List<int> month14;
        private static List<int> month7;
        private static Dictionary<int, string> leapList;
        private static Dictionary<int, string> commonList;
        public static string test = "Test";

        public Dictionary<int, string> MonthList
        {
            get
            {
                if (dt.isleapyear())
                {
                    return LeapList;
                }
                else
                {
                    return CommonList;
                }
            }
        }

        public List<int> DayList
        {
            get
            {
                if (dt.Month != 14)
                {
                    if (month28 == null)
                    {
                        month28 = new List<int>();
                        int i = 1;
                        while (i < 29)
                        {
                            month28.Add(i++);
                        }
                    }
                    return month28;
                }
                else if (dt.isDoubleLeapYear())
                {
                    if (month14 == null)
                    {
                        month14 = new List<int>();
                        int i = 1;
                        while (i < 15)
                        {
                            month14.Add(i++);
                        }
                    }
                    return month14;
                }
                else
                {
                    if (month7 == null)
                    {
                        month7 = new List<int>();
                        int i = 1;
                        while (i < 8)
                        {
                            month7.Add(i++);
                        }
                    }
                    return month7;
                }
            }
        }

        public int Horus
        {
            get
            {
                if (dt.isDoubleLeapYear())
                {
                    return 14;
                }
                else if (dt.isleapyear())
                {
                    return 7;
                }
                else
                {
                    return 0;
                }
            }
        }

        public Dictionary<int, string> CommonList
        {
            get
            {
                if (commonList == null)
                {
                    GenerateLists();
                }
                return commonList;
            }
        }

        public Dictionary<int, string> LeapList
        {
            get
            {
                if (leapList == null)
                {
                    GenerateLists();
                }
                return leapList;
            }
        }

        public string DisplayName { get; private set; } = "InputStarDate";

        private void GenerateLists()
        {
            leapList = new Dictionary<int, string>();
            commonList = new Dictionary<int, string>();
            int i = 0;
            int j = 13;
            while (i < j)
            {
                string s = StarCulture.MonthSymbols[i] + " " + StarCulture.CurrentCulture.GetMonthNameFromIndex(i);
                commonList.Add(i + 1, s);
                leapList.Add(i + 1, s);
                i++;
            }
            leapList.Add(14, StarCulture.MonthSymbols[13] + " " + StarCulture.CurrentCulture.GetMonthNameFromIndex(13));
        }

        public override string ToString()
        {
            return dt;
        }
    }
}
