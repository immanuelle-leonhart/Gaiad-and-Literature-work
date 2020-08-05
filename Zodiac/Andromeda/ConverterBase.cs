using Microsoft.AspNetCore.Components;
using StarLib;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Zodiac.Andromeda
{
    public class ConverterBase : ComponentBase
    {
        private StarDate sd;
        private DateTime dt;

        public StarDate CosmicDate
        {
            get => sd;
            set
            {
                sd = value;
                dt = value;
            }
        }
        public DateTime GregDate
        {
            get => dt;
            set
            {
                dt = value;
                sd = value;
            }
        }

        protected override void OnInitialized()
        {
            sd = StarDate.Now;
            dt = DateTime.Now;
        }
    }
}
