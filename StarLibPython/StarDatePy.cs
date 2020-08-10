using StarLib;
using System;
using System.Dynamic;

namespace StarLibPython
{
    public class StarDatePy : DynamicObject
    {
        StarDate starDate;
        public StarDatePy()
        {
            starDate = StarDate.Now;
        }

        public StarDatePy(string data)
        {
            starDate = new StarDate(data);
        }

        public StarDatePy(StarDate v)
        {
            starDate = v;
        }

        public override bool TryGetMember(GetMemberBinder binder, out object result)
        {
            result = null;
            switch (binder.Name)
            {
                case "AddDays":
                    result = (Func<double, StarDatePy>)((double a)
                          => starDate.AddDays(a));
                    return true;
                case "ToLongString":
                    result = (Func<string>)(()
                          => starDate.ToLongString());
                    return true;
            }
            return false;
        }

        public static implicit operator StarDatePy(StarDate v)
        {
            return new StarDatePy(v);
        }
    }
}
