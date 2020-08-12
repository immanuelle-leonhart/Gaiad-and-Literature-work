using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace StarLib
{
    public class StarDateConverter : JsonConverter<StarDate>
    {
        public override void WriteJson(JsonWriter writer, StarDate value, JsonSerializer serializer)
        {
            writer.WriteValue(value.ToString());
        }

        public override StarDate ReadJson(JsonReader reader, Type objectType, StarDate existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            string s = (string)reader.Value;

            return new StarDate(s);
        }
    }

    public class StarCultureConverter : JsonConverter<StarCulture>
    {
        public override void WriteJson(JsonWriter writer, StarCulture value, JsonSerializer serializer)
        {
            writer.WriteValue(value.ToString());
        }

        public override StarCulture ReadJson(JsonReader reader, Type objectType, StarCulture existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            string s = (string)reader.Value;
            throw new NotImplementedException();
            //return new StarCulture(s);
        }
    }

    public class StarZoneConverter : JsonConverter<StarZone>
    {
        public override void WriteJson(JsonWriter writer, StarZone value, JsonSerializer serializer)
        {
            writer.WriteValue(value.ToString());
        }

        public override StarZone ReadJson(JsonReader reader, Type objectType, StarZone existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            string s = (string)reader.Value;

            return new StarZone(s);
        }
    }
}
