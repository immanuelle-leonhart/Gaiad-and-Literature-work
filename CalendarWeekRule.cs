// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==


using System;

namespace StarCalendar
{
    public class CalendarWeekRule
    {
        public CalendarWeekRule FirstDay { get; internal set; }

        public static explicit operator CalendarWeekRule(int v)
        {
            throw new NotImplementedException();
        }
    }
}