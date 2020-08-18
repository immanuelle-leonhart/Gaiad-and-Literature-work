// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==
////////////////////////////////////////////////////////////////////////////
//
//  Class:    StarDateParse
//
//  Purpose:  This class is called by StarDate to parse a date/time string.
//
////////////////////////////////////////////////////////////////////////////

namespace StarLib
{
    internal class TimeZoneInfoOptions
    {
        public static StarZoneOptions NoThrowOnInvalidTime { get; internal set; }
    }
}