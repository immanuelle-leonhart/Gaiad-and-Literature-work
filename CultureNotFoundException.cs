// ==++==
//
//   Copyright (c) Microsoft Corporation.  All rights reserved.
//
// ==--==


using System;
using System.Runtime.Serialization;

namespace StarCalendar
{
    [Serializable]
    internal class CultureNotFoundException : Exception
    {
        private string v;
        private string m_name;
        private object p;

        public CultureNotFoundException()
        {
        }

        public CultureNotFoundException(string message) : base(message)
        {
        }

        public CultureNotFoundException(string message, Exception innerException) : base(message, innerException)
        {
        }

        public CultureNotFoundException(string v, string m_name, object p)
        {
            this.v = v;
            this.m_name = m_name;
            this.p = p;
        }

        protected CultureNotFoundException(SerializationInfo info, StreamingContext context) : base(info, context)
        {
        }
    }
}