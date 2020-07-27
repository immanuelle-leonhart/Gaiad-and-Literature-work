using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace StarBlaze.Client
{
    public class StarDateConverter
    {
        private DateTime dateTime;

        public StarDateConverter()
        {
            this.DateTime = DateTime.Now;
        }

        public DateTime DateTime { get => dateTime; set => dateTime = value; }
    }
}
