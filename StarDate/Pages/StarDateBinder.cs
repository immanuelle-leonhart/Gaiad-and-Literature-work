// Copyright (c) .NET Foundation. All rights reserved.
// Licensed under the Apache License, Version 2.0. See License.txt in the project root for license information.

using StarLib;
using System;
using System.Globalization;

namespace StarBlaze
{
    public class StarDateBinder
    {
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
        /// Attempts to convert a value to a <see cref="System.StarDate"/>.
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
            if (string.IsNullOrEmpty(text))
            {
                value = default;
                return false;
            }

            if (format != null && StarDate.TryParseExact(text, format, culture ?? CultureInfo.CurrentCulture, StarDateStyles.None, out var converted))
            {
                value = converted;
                return true;
            }
            else if (format == null && StarDate.TryParse(text, culture ?? CultureInfo.CurrentCulture, StarDateStyles.None, out converted))
            {
                value = converted;
                return true;
            }

            value = default;
            return false;
        }

    }
}