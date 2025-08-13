using System;
using System.Collections.Generic;
using System.Text;
using System.Dynamic;

namespace DynamicCS
{
    public class DynamicCalc : DynamicObject
    {
        Calculator calc;
        public DynamicCalc()
        {
            calc = new Calculator();
        }
        public override bool TryGetMember(GetMemberBinder binder, out object result)
        {
            result = null;
            switch (binder.Name)
            {
                case "add":
                    result = (Func<double, double, double>)((double a, double b)
                          => calc.add(a, b));
                    return true;
                case "sub":
                    result = (Func<double, double, double>)((double a, double b)
                          => calc.sub(a, b));
                    return true;
            }
            return false;
        }
    }
}
