// Copyright (c) .NET Foundation. All rights reserved.
// Licensed under the Apache License, Version 2.0. See License.txt in the project root for license information.

using System;
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
    /// Supported types are <see cref="DateTime"/> and <see cref="StarDate"/>.
    /// </summary>
    public class InputStarDate<TValue> : InputBase<TValue>
    {
        private const string DateFormat = "yyyy-MM-dd"; // Compatible with HTML date inputs
        //protected StarDate dt;

        /// <summary>
        /// Gets or sets the error message used when displaying an a parsing error.
        /// </summary>
        [Parameter] public string ParsingErrorMessage { get; set; } = "The {0} field must be a StarDate.";

        /// <inheritdoc />
        protected override string FormatValueAsString([AllowNull] TValue value)
        {
            switch (value)
            {
                case DateTime dateTimeValue:
                    return BindConverter.FormatValue(dateTimeValue, DateFormat, CultureInfo.InvariantCulture);
                case StarDate StarDateValue:
                    return BindConverter.FormatValue(StarDateValue, DateFormat, CultureInfo.InvariantCulture);
                default:
                    return string.Empty; // Handles null for Nullable<DateTime>, etc.
            }
        }

        /// <inheritdoc />
        protected override bool TryParseValueFromString(string? value, [MaybeNull] out TValue result, [NotNullWhen(false)] out string? validationErrorMessage)
        {
            // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
            // types here, because the underlying InputBase already covers that.
            var targetType = Nullable.GetUnderlyingType(typeof(TValue)) ?? typeof(TValue);

            bool success;
            if (targetType == typeof(DateTime))
            {
                success = TryParseDateTime(value, out result);
            }
            else if (targetType == typeof(StarDate))
            {
                success = TryParseStarDate(value, out result);
            }
            else
            {
                throw new InvalidOperationException($"The type '{targetType}' is not a supported date type.");
            }

            if (success)
            {
                validationErrorMessage = null;
                return true;
            }
            else
            {
                validationErrorMessage = string.Format(ParsingErrorMessage, "InputStarDate" ?? FieldIdentifier.FieldName);
                return false;
            }
        }

        static bool TryParseDateTime(string? value, [MaybeNullWhen(false)] out TValue result)
        {
            var success = BindConverter.TryConvertToDateTime(value, CultureInfo.InvariantCulture, DateFormat, out var parsedValue);
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

        static bool TryParseStarDate(string? value, [MaybeNullWhen(false)] out TValue result)
        {
            var success = StarDateBinder.TryConvertToStarDate(value, CultureInfo.InvariantCulture, DateFormat, out var parsedValue);
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

        

        
    }
}
