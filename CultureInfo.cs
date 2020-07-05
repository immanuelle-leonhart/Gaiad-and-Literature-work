// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==
using System;

namespace StarCalendar
{
    internal class CultureInfo
    {
        internal static CultureInfo InvariantCulture;
        internal StarDateTimeFormatInfo DateTimeFormat;

        public static IFormatProvider CurrentCulture { get; internal set; }
        public StarDateTimeFormatInfo StarDateFormat { get; internal set; }

        internal IFormatProvider GetFormat()
        {
            throw new NotImplementedException();
        }
    }
}