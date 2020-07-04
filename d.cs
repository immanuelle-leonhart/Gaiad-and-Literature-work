using System;

namespace StarCalendar
{
    internal static class d
    {
        internal static string planetstring = "Terra";
        internal static TimeSpanInfo offset = new TimeSpanInfo(TimeZoneInfo.Local.BaseUtcOffset);
        internal static string format = "numeric";
        internal static string lang = "English";

        internal static string defaultformat()
        {
            return format;
        }

        internal static Locale getlocale()
        {
            return Locale.GetLocale(lang);
        }

        //internal static string[] months = new string[14]
        //{
        //    "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Karkino", "Leo", "Virgo", "Libra", "Scorpio", "Ophiuchus",  "Horus"
        //};

        //internal static string[] monthshort = new string[14]
        //{
        //    "SAG", "CAP", "AQU", "PIS", "ARI", "TAU", "GEM", "KAR", "LEO", "VIR", "LIB", "SCO", "OPH", "HOR"
        //};

        //internal static string[] weekdays = new string[7]
        //{
        //    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
        //};

        //internal static string[] weekdayshort = new string[7]
        //{
        //    "SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"
        //};


    }
}