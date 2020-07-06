// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==


using System;

namespace StarCalendar
{
    public class Calendar
    {
        public int ID { get; internal set; }
        public int CurrentEraValue { get; internal set; }
        public int CAL_JAPAN { get; internal set; }
        public int CAL_TAIWAN { get; internal set; }
        public object MinSupportedStarDate { get; internal set; }
        public object MaxSupportedStarDate { get; internal set; }

        internal Calendar GetDefaultInstance()
        {
            throw new NotImplementedException();
        }

        internal Calendar Clone()
        {
            throw new NotImplementedException();
        }

        internal void SetReadOnlyState(bool m_isReadOnly)
        {
            throw new NotImplementedException();
        }

        internal Calendar ReadOnly(Calendar calendar)
        {
            throw new NotImplementedException();
        }

        internal int GetYear(object minSupportedStarDate)
        {
            throw new NotImplementedException();
        }

        //internal int GetYear(object maxSupportedStarDate)
        //{
        //    throw new NotImplementedException();
        //}

        internal bool IsLeapYear(int year)
        {
            throw new NotImplementedException();
        }
    }
}