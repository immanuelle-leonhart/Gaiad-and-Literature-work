using Newtonsoft.Json.Serialization;
using StarLib;
using System;
using System.Dynamic;
using System.Numerics;

namespace StarLib.Dynamic
{
    public class StarDateDynamic : DynamicObject
    {
        StarDate starDate;
        public StarDateDynamic()
        {
            starDate = StarDate.Now;
        }

        public StarDateDynamic(string data)
        {
            starDate = new StarDate(data);
        }

        public StarDateDynamic(StarDate v)
        {
            starDate = v;
        }

        public override bool TrySetMember(SetMemberBinder binder, object value)
        {
            switch (binder.Name)
            {
                case "Fullyear":
                    starDate.Fullyear = (long)value;
                    return true;
                case "Quadrillion":
                    starDate.Quadrillion = (int)value;
                    return true;
                case "Trillion":
                    starDate.Trillion = (int)value;
                    return true;
                case "Billion":
                    starDate.Billion = (int)value;
                    return true;
                case "Million":
                    starDate.Million = (int)value;
                    return true;
                case "Year":
                    starDate.Year = (int)value;
                    return true;
                case "DayOfYear":
                    starDate.DayOfYear = (int)value;
                    return true;
                case "Month":
                    starDate.Month = (int)value;
                    return true;
                case "Day":
                    starDate.Day = (int)value;
                    return true;
                case "Hour":
                    starDate.Hour = (int)value;
                    return true;
                case "Minute":
                    starDate.Minute = (int)value;
                    return true;
                case "Second":
                    starDate.Second = (int)value;
                    return true;
                case "Millisecond":
                    starDate.Millisecond = (int)value;
                    return true;
                case "Ticks":
                    starDate.Ticks = (BigInteger)value;
                    return true;
                case "Julian":
                    starDate.Julian = (long)value;
                    return true;
            }
            return false;
        }

        public override bool TryGetMember(GetMemberBinder binder, out object result)
        {
            result = null;
            switch (binder.Name)
            {
                case "UtcNow":
                    result = (Func<StarDateDynamic>)(()
                          => StarDate.UtcNow);
                    return true;
                case "Now":
                    result = (Func<StarDateDynamic>)(()
                          => StarDate.Now);
                    return true;
                case "Fullyear":
                    result = (Func<long>)(()
                          => starDate.Fullyear);
                    return true;
                case "Quadrillion":
                    result = (Func<int>)(()
                          => starDate.Quadrillion);
                    return true;
                case "Trillion":
                    result = (Func<int>)(()
                          => starDate.Trillion);
                    return true;
                case "Billion":
                    result = (Func<int>)(()
                          => starDate.Billion);
                    return true;
                case "Million":
                    result = (Func<int>)(()
                          => starDate.Million);
                    return true;
                case "Year":
                    result = (Func<int>)(()
                          => starDate.Year);
                    return true;
                case "Month":
                    result = (Func<int>)(()
                          => starDate.Month);
                    return true;
                case "DayOfYear":
                    result = (Func<int>)(()
                          => starDate.DayOfYear);
                    return true;
                case "Day":
                    result = (Func<int>)(()
                          => starDate.Day);
                    return true;
                case "Hour":
                    result = (Func<int>)(()
                          => starDate.Hour);
                    return true;
                case "Minute":
                    result = (Func<int>)(()
                          => starDate.Minute);
                    return true;
                case "Second":
                    result = (Func<int>)(()
                          => starDate.Second);
                    return true;
                case "Millisecond":
                    result = (Func<int>)(()
                          => starDate.Hour);
                    return true;
                case "ExtraTicks":
                    result = (Func<int>)(()
                          => starDate.ExtraTicks);
                    return true;
                case "Ticks":
                    result = (Func<BigInteger>)(()
                          => starDate.Ticks);
                    return true;
                case "Julian":
                    result = (Func<long>)(()
                          => starDate.Julian);
                    return true;
                case "MonthSymbol":
                    result = (Func<string>)(()
                          => starDate.MonthSymbol);
                    return true;
                case "MonthName":
                    result = (Func<string>)(()
                          => starDate.MonthName);
                    return true;
                case "DaySymbol":
                    result = (Func<string>)(()
                          => starDate.DaySymbol);
                    return true;
                case "DayName":
                    result = (Func<string>)(()
                          => starDate.DayName);
                    return true;
                case "ToLongString":
                    result = (Func<string>)(()
                          => starDate.ToLongString());
                    return true;
                case "ToShortString":
                    result = (Func<string>)(()
                          => starDate.ToShortString());
                    return true;
                case "BasicString":
                    result = (Func<string>)(()
                          => starDate.BasicString());
                    return true;
                case "AddYears":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddYears(a));
                    return true;
                case "AddMonths":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddMonths(a));
                    return true;
                case "AddWeeks":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddWeeks(a));
                    return true;
                case "AddDays":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddDays(a));
                    return true;
                case "AddHours":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddHours(a));
                    return true;
                case "AddMinutes":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddMinutes(a));
                    return true;
                case "AddSeconds":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddSeconds(a));
                    return true;
                case "AddMilliseconds":
                    result = (Func<double, StarDateDynamic>)((double a)
                          => starDate.AddMilliseconds(a));
                    return true;
                case "AddTicks":
                    result = (Func<int, StarDateDynamic>)((int a)
                          => starDate.AddTicks(a));
                    return true;
                case "GetDateParts":
                    result = (Func<int, int[]>)((int a)
                          => starDate.GetDateParts(a));
                    return true;
                case "Equals":
                    result = (Func<StarDateDynamic, bool>)((StarDateDynamic d)
                          => starDate.Equals(d.starDate));
                    return true;
                case "CompareTo":
                    result = (Func<StarDateDynamic, int>)((StarDateDynamic d)
                          => starDate.CompareTo(d.starDate));
                    return true;
            }
            return false;
        }

        public static implicit operator StarDateDynamic(StarDate v)
        {
            return new StarDateDynamic(v);
        }
    }
}
