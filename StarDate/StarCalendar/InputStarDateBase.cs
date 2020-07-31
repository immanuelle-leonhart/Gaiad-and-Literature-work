﻿// Copyright (c) .NET Foundation. All rights reserved.
// Licensed under the Apache License, Version 2.0. See License.txt in the project root for license information.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Forms;
using Microsoft.AspNetCore.Components.Rendering;
using StarLib;

namespace StarBlaze.StarCalendar
{
    /// <summary>
    /// An input component for editing date values.
    /// Supported types are <see cref="DateTime"/> and <see cref="DateTimeOffset"/>.
    /// </summary>
    public class InputStarDateBase<TValue> : InputBase<TValue>
    {
        private const int PlaceHolder = 9999999;

        protected StarDate dt = StarDate.Now;
        private static List<int> month28;
        private static List<int> month14;
        private static List<int> month7;
        private static Dictionary<int, string> leapList;
        private static Dictionary<int, string> commonList;
        public static string test = "Test";

        public int Year { get => dt.Year; set => dt.Year = value; }
        public int Month { get => dt.Month; set => dt.Month = value; }
        public int Day { get => dt.Day; set => dt.Day = value; }
        public int Hour { get => dt.Hour; set => dt.Hour = value; }
        public int Minute { get => dt.Minute; set => dt.Minute = value; }
        public int Second { get => dt.Second; set => dt.Second = value; }
        public string Short { get => dt.ToShortString(); }
        public string Long { get => dt.ToLongString(); }

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
                if (Month != 14)
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




























        /// <summary>
        /// Legacy
        /// </summary>
        /// <param name="builder"></param>
        //protected override void BuildRenderTree(RenderTreeBuilder builder)
        //{
        //    builder.OpenElement(0, "input");
        //    builder.AddMultipleAttributes(1, AdditionalAttributes);
        //    builder.AddAttribute(2, "type", "date");
        //    builder.AddAttribute(3, "class", CssClass);
        //    builder.AddAttribute(4, "value", BindConverter.FormatValue(CurrentValueAsString));
        //    builder.AddAttribute(5, "onchange", EventCallback.Factory.CreateBinder<string?>(this, __value => CurrentValueAsString = __value, CurrentValueAsString));
        //    builder.CloseElement();
        //}

        protected override bool TryParseValueFromString(string value, out TValue result, out string validationErrorMessage)
        {
            // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
            // types here, because the underlying InputBase already covers that.
            var targetType = Nullable.GetUnderlyingType(typeof(TValue)) ?? typeof(TValue);

            bool success;
            //if (targetType == typeof(StarDate))
            //{
            success = TryParseDateTime(value, out result);
            //}

            if (success)
            {
                validationErrorMessage = null;
                return true;
            }
            else
            {
                validationErrorMessage = "Error";
                return false;
            }

        }

        static bool TryParseDateTime(string? value, [MaybeNullWhen(false)] out TValue result)
        {
            var success = TryConvertToStarDate(value, out var parsedValue);
            if (success)
            {
                result = (TValue)(object)parsedValue;
                return true;
            }
            else
            {
                result = default;
                return false;
            }
        }

        public static bool TryConvertToStarDate(object? obj, out StarDate value)
        {
            string va = (string)obj;
            List<string> vs = new List<string> { "" };
            int i = 0;
            foreach (char n in va)
            {
                if (char.IsDigit(n))
                {
                    vs[i] += n;
                }
                else
                {
                    i++;
                    vs.Add("");
                }
            }
            int[] q = new int[] { PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder };
            i = 0;
            while ((i < q.Length) && (i < vs.Count))
            {
                q[i] = int.Parse(vs[i], CultureInfo.InvariantCulture);
                i++;
            }
            value = new StarDate(q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]);
            return true;
        }
    }
}