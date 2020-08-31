using System;
using System.Collections.Generic;
using System.Dynamic;
using System.Text;
using StarLib;

/// <summary>
/// https://www.red-gate.com/simple-talk/dotnet/net-framework/dynamic-language-integration-in-a-c-world/
/// </summary>

namespace StarLib.Dynamic
{
    class StarCultureDynamic : DynamicObject
    {
        StarLib.StarCulture culture;
    }
}
