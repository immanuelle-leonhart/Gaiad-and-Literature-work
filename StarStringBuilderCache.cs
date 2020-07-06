// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==
using System;
using System.Text;

namespace StarCalendar
{
    public class StarStringBuilderCache
    {
        internal StringBuilder Acquire(int rfc1123FormatLength)
        {
            throw new NotImplementedException();
        }

        internal string GetStringAndRelease(StringBuilder stringBuilder)
        {
            throw new NotImplementedException();
        }

        internal StringBuilder Acquire()
        {
            throw new NotImplementedException();
        }
    }
}