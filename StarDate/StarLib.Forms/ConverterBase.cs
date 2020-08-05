using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Forms;
using StarLib;
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading.Tasks;

namespace StarLib.Forms
{
    public class ConverterBase : ComponentBase
    {
        private StarDate star = StarDate.Now;
        private DateTime date = DateTime.Now;

        public StarDate sd
        {
            get => star; set
            {
                star = value;
                date = value.DateTime;
            }
        }
        public DateTime dt
        {
            get => date; set
            {
                date = value;
                star = new StarDate(value);
            }
        }
    }
}
