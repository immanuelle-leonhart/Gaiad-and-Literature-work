using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace StarLib
{
    public class StarDateConverter : JsonConverter<StarDate>
    {
        public override void WriteJson(JsonWriter writer, StarDate value, JsonSerializer serializer)
        {
            throw new NotImplementedException();
            JToken t = JToken.FromObject(value);

            if (t.Type != JTokenType.Object)
            {
                t.WriteTo(writer);
            }
            else
            {
                JObject o = (JObject)t;
                IList<string> propertyNames = o.Properties().Select(p => p.Name).ToList();

                o.AddFirst(new JProperty("Keys", new JArray(propertyNames)));

                o.WriteTo(writer);
            }
        }

        public override StarDate ReadJson(JsonReader reader, Type objectType, StarDate existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            throw new NotImplementedException();
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
