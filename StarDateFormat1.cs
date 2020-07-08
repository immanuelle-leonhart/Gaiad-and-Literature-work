// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==
using System;
using System.Globalization;

namespace StarCalendar
{
    public class StarDateFormat1
    {
        internal string[] AbbreviatedDayNames;
        internal string[] AbbreviatedMonthNames;
        //internal static StarDateFormat InvariantCulture;

        public object Calendar { get; internal set; }
        public string ShortDatePattern { get; internal set; }
        public string LongDatePattern { get; internal set; }
        public string FullStarDatePattern { get; internal set; }
        public string GeneralShortTimePattern { get; internal set; }
        public string GeneralLongTimePattern { get; internal set; }
        public string MonthDayPattern { get; internal set; }
        public string RFC1123Pattern { get; internal set; }
        public string SortableStarDatePattern { get; internal set; }
        public string ShortTimePattern { get; internal set; }
        public string LongTimePattern { get; internal set; }
        public string UniversalSortableStarDatePattern { get; internal set; }
        public string YearMonthPattern { get; internal set; }
        public string StarDateOffsetPattern { get; internal set; }

        internal string GetAbbreviatedDayName(DayOfWeek dayOfWeek)
        {
            throw new NotImplementedException();
        }

        internal string GetDayName(DayOfWeek dayOfWeek)
        {
            throw new NotImplementedException();
        }

        internal string GetAbbreviatedMonthName(int month)
        {
            throw new NotImplementedException();
        }

        internal string Format(StarDate dt, string format, DateTimeFormatInfo currentInfo)
        {
            throw new NotImplementedException();
        }

        internal string GetMonthName(int month)
        {
            throw new NotImplementedException();
        }

        internal StarDateFormat Clone()
        {
            throw new NotImplementedException();
        }

        internal string[] GetAllStarDatePatterns(char format)
        {
            throw new NotImplementedException();
        }
    }
}