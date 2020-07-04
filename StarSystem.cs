using System;
using System.Collections.Generic;
using System.Numerics;

namespace GaianEmpire
{
    public class StarSystem
    {
        //private static string type = "standard";
        //public BigInteger atomicTicks; //atomic atomicTime ticks
        public StarDate startDate; //atomicTime that movement starts
        public List<BigInteger> distanceTicks = new List<BigInteger>(); //position, speed, acceleration, etc
        public List<double> polar = new List<double>(); //position, speed, acceleration, etc
        public List<double> azimuthal = new List<double>(); //position, speed, acceleration, etc
        public string name;

        public double[] cartesian()
        {
            double x = (long)distanceTicks[0] * Math.Sin(polar[0]) * Math.Cos(azimuthal[0]);
            double y = (long)distanceTicks[0] * Math.Sin(polar[0]) * Math.Sin(azimuthal[0]);
            double z = (long)distanceTicks[0] * Math.Cos(polar[0]);
            return new double[] { x, y, z };
        }

        public StarSystem(StarDate startDate, List<BigInteger> distanceTicks, List<double> polar, List<double> azimuthal)
        {
            this.startDate = startDate;
            this.distanceTicks = distanceTicks;
            this.polar = polar;
            this.azimuthal = azimuthal;
        }

        public StarSystem(string name)
        {
            this.name = name;
            this.startDate = new StarDate(0);
            this.distanceTicks = new List<BigInteger> { 0 };
            this.azimuthal = new List<double> { 0 };
            this.polar = new List<double> { 0 };
        }

        internal object distance_at_time(StarDate now)
        {
            throw new NotImplementedException();
        }
    }
}