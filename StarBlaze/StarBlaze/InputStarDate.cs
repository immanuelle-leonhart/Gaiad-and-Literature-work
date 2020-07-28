// Copyright (c) .NET Foundation. All rights reserved.
// Licensed under the Apache License, Version 2.0. See License.txt in the project root for license information.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Forms;
using Microsoft.AspNetCore.Components.Rendering;
using StarLib;

namespace StarBlaze
{
    /// <summary>
    /// An input component for editing date values.
    /// Supported types are <see cref="DateTime"/> and <see cref="DateTimeOffset"/>.
    /// </summary>
    public class InputStarDate<TValue> : InputBase<TValue>
    {
        private const int PlaceHolder = 9999999;

        /// <inheritdoc />
        protected override void BuildRenderTree(RenderTreeBuilder builder)
        {
            builder.OpenElement(0, "input");
            builder.AddMultipleAttributes(1, AdditionalAttributes);
            builder.AddAttribute(2, "type", "date");
            builder.AddAttribute(3, "class", CssClass);
            builder.AddAttribute(4, "value", BindConverter.FormatValue(CurrentValueAsString));
            builder.AddAttribute(5, "onchange", EventCallback.Factory.CreateBinder<string?>(this, __value => CurrentValueAsString = __value, CurrentValueAsString));
            builder.CloseElement();
        }

        protected override bool TryParseValueFromString(string value, out TValue result, out string validationErrorMessage)
        {
            // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
            // types here, because the underlying InputBase already covers that.
            var targetType = Nullable.GetUnderlyingType(typeof(TValue)) ?? typeof(TValue);

            bool success;
            //if (targetType == typeof(StarDate))
            //{
                success = TryParseDateTime(value, out result);
            //}

            if (success)
            {
                validationErrorMessage = null;
                return true;
            }
            else
            {
                validationErrorMessage = "Error";
                return false;
            }

        }

        static bool TryParseDateTime(string? value, [MaybeNullWhen(false)] out TValue result)
        {
            var success = TryConvertToStarDate(value, out var parsedValue);
            if (success)
            {
                result = (TValue)(object)parsedValue;
                return true;
            }
            else
            {
                result = default;
                return false;
            }
        }

        public static bool TryConvertToStarDate(object? obj, out StarDate value)
        {
            string va = (string)obj;
            List<string> vs = new List<string> { "" };
            int i = 0;
            foreach (char n in va)
            {
                if (char.IsDigit(n))
                {
                    vs[i] += n;
                }
                else
                {
                    i++;
                    vs.Add("");
                }
            }
            int[] q = new int[] { PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder, PlaceHolder };
            i = 0;
            while ((i < q.Length) && (i < vs.Count))
            {
                q[i] = int.Parse(vs[i], CultureInfo.InvariantCulture);
                i++;
            }
            value = new StarDate(q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]);
            return true;
        }
    }
}