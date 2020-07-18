using System;
using System.Collections.Generic;
using System.Data.SqlTypes;
using System.Diagnostics.CodeAnalysis;
using System.Diagnostics.SymbolStore;
using System.Runtime.CompilerServices;

namespace GaianEmpire
{
    public struct StarDate
    {
        public TimeSpanInfo time;
        public StarDate(DateTime now)
        {
            //throw new NotImplementedException();
        }

        public StarDate(int year, int month, int day)
        {
            //throw new NotImplementedException();
        }

        public override string ToString()
        {
            //throw new NotImplementedException();
        }

        public static StarDate Now()
        {
            return new StarDate(DateTime.Now);
        }

        public DateTime Convert()
        {

        }


    }
}