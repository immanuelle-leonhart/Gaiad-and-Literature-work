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
    /// Supported types are <see cref="DateTime"/> and <see cref="DateTimeOffset"/>.
    /// </summary>
    public class InputStarDate<TValue> : InputBase<TValue>
    {
        private const string DateFormat = "yyyy-MM-dd"; // Compatible with HTML date inputs

        /// <summary>
        /// Gets or sets the error message used when displaying an a parsing error.
        /// </summary>
        [Parameter] public string ParsingErrorMessage { get; set; } = "The {0} field must be a date.";
        public string DisplayName { get; private set; }

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

        /// <inheritdoc />
        protected override string FormatValueAsString([AllowNull] TValue value)
        {
            switch (value)
            {
                case DateTime dateTimeValue:
                    return BindConverter.FormatValue(dateTimeValue, DateFormat, CultureInfo.InvariantCulture);
                case DateTimeOffset dateTimeOffsetValue:
                    return BindConverter.FormatValue(dateTimeOffsetValue, DateFormat, CultureInfo.InvariantCulture);
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
            if (targetType == typeof(StarDate))
            {
                success = TryParseStarDate(value, out result);
            }
            else if (targetType == typeof(DateTime))
            {
                success = TryParseDateTime(value, out result);
            }
            else if (targetType == typeof(DateTimeOffset))
            {
                success = TryParseDateTimeOffset(value, out result);
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
                validationErrorMessage = string.Format(ParsingErrorMessage, DisplayName ?? FieldIdentifier.FieldName);
                return false;
            }
        }

        static bool TryParseStarDate(string? value, [MaybeNullWhen(false)] out TValue result)
        {
            var success = TryConvertToStarDate(value, CultureInfo.InvariantCulture, DateFormat, out var parsedValue);
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

        static bool TryParseDateTimeOffset(string? value, [MaybeNullWhen(false)] out TValue result)
        {
            var success = BindConverter.TryConvertToDateTimeOffset(value, CultureInfo.InvariantCulture, DateFormat, out var parsedValue);
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

        /// <summary>
        /// Attempts to convert a value to a <see cref="System.StarDate"/>.
        /// </summary>
        /// <param name="obj">The object to convert.</param>
        /// <param name="culture">The <see cref="CultureInfo"/> to use for conversion.</param>
        /// <param name="value">The converted value.</param>
        /// <returns><c>true</c> if conversion is successful, otherwise <c>false</c>.</returns>
        public static bool TryConvertToStarDate(object? obj, CultureInfo? culture, out StarDate value)
        {
            return ConvertToStarDateCore(obj, culture, out value);
        }

        /// <summary>
        /// Attempts to convert a value to a <see cref="System.DateTime"/>.
        /// </summary>
        /// <param name="obj">The object to convert.</param>
        /// <param name="culture">The <see cref="CultureInfo"/> to use for conversion.</param>
        /// <param name="format">The format string to use in conversion.</param>
        /// <param name="value">The converted value.</param>
        /// <returns><c>true</c> if conversion is successful, otherwise <c>false</c>.</returns>
        public static bool TryConvertToStarDate(object? obj, CultureInfo? culture, string format, out StarDate value)
        {
            return ConvertToStarDateCore(obj, culture, format, out value);
        }

        private static bool ConvertToStarDateCore(object? obj, CultureInfo? culture, out StarDate value)
        {
            return ConvertToStarDateCore(obj, culture, format: null, out value);
        }

        private static bool ConvertToStarDateCore(object? obj, CultureInfo? culture, string? format, out StarDate value)
        {
            var text = (string?)obj;
            return StarDate.TryDashParse(text, out value);
            //if (string.IsNullOrEmpty(text))
            //{
            //    value = default;
            //    return false;
            //}

            //if (format != null && StarDate.TryParse(text, format, culture ?? CultureInfo.CurrentCulture, StarDateStyles.None, out var converted))
            //{
            //    value = (StarDate)converted;
            //    return true;
            //}
            //else if (format == null && StarDate.TryParse(text, culture ?? CultureInfo.CurrentCulture, StarDateStyles.None, out var converted))
            //{
            //    value = (StarDate)converted;
            //    return true;
            //}

            //value = default;
            //return false;
        }
    }
}