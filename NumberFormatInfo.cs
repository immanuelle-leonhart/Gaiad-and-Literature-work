// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==


using System;

namespace StarCalendar
{
    internal class NumberFormatInfo
    {
        private CultureInfo cultureDataWithoutUserOverrides;

        public NumberFormatInfo(CultureInfo cultureDataWithoutUserOverrides)
        {
            this.cultureDataWithoutUserOverrides = cultureDataWithoutUserOverrides;
        }

        public static IFormatProvider InvariantInfo { get; internal set; }
        public string NumberDecimalSeparator { get; internal set; }
    }
}