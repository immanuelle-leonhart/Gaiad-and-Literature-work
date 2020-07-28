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
    public class InputStarDate<StarDate> : InputBase<StarDate>
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

        protected override bool TryParseValueFromString(string value, out StarDate result, out string validationErrorMessage)
        {
            List<string> vs = new List<string> { "" };
            int i = 0;
            foreach (char n in value)
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
            result = new StarDate(q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]);
            validationErrorMessage = null;
            return true;
        }


    }
}