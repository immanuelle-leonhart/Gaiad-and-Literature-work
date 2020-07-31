// Copyright (c) .NET Foundation. All rights reserved.
// Licensed under the Apache License, Version 2.0. See License.txt in the project root for license information .

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq.Expressions;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Forms;
using Microsoft.AspNetCore.Components.Rendering;
using StarLib;

namespace StarBlaze
{
    /// <summary>
    /// An input component for editing date values.
    /// Supported types are <see cref="StarDate"/> and <see cref="StarDateOffset"/>.
    /// </summary>
    public class InputStarDate<TValue> : InputBase<TValue>
    {
        private const string DateFormat = "yyyy-MM-dd"; // Compatible with HTML date inputs
        private string displayName;

        //private TValue /*value*/ = default;

        /// <summary>
        /// Gets or sets the error message used when displaying an a parsing error.
        /// </summary>
        [Parameter] public string ParsingErrorMessage { get; set; } = "The {0} field must be a date.";
        //public string DisplayName { get; private set; }

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
                case StarDate StarDateValue:
                    return BindConverter.FormatValue(StarDateValue, DateFormat, CultureInfo.InvariantCulture);
                //case StarDateOffset StarDateOffsetValue:
                //    return BindConverter.FormatValue(StarDateOffsetValue, DateFormat, CultureInfo.InvariantCulture);
                default:
                    return string.Empty; // Handles null for Nullable<StarDate>, etc.
            }
        }

        /// <inheritdoc />
        protected override bool TryParseValueFromString(string? value, [MaybeNull] out TValue result, [NotNullWhen(false)] out string? validationErrorMessage)
        {
            if (value is null)
            {
                throw new ArgumentNullException(nameof(value));
            }
            // Unwrap nullable types. We don't have to deal with receiving empty values for nullable
            // types here, because the underlying InputBase already covers that.
            var targetType = Nullable.GetUnderlyingType(typeof(TValue)) ?? typeof(TValue);

            bool success;
            if (targetType == typeof(StarDate))
            {
                success = TryParseStarDate(value, out result);
            }
            //else if (targetType == typeof(StarDateOffset))
            //{
            //    success = TryParseStarDateOffset(value, out result);
            //}
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
            if (string.IsNullOrWhiteSpace(value))
            {
                throw new ArgumentException("message", nameof(value));
            }

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

        private static bool TryConvertToStarDate(string value, CultureInfo invariantCulture, string dateFormat, out object parsedValue)
        {
            throw new NotImplementedException();
        }

        /// <summary>
        /// Gets or sets the value of the input. This should be used with two-way binding.
        /// </summary>
        /// <example>
        /// @bind-Value="model.PropertyName"
        /// </example>
        [AllowNull]
        [MaybeNull]
        [Parameter]
        public new TValue Value
        {
            get
            {
                //return value;
                throw new NotImplementedException();
            }

            set
            {
                //value = value;
                throw new NotImplementedException();
            }
        }
        /// <summary>
        /// Gets or sets a callback that updates the bound value.
        /// </summary>
        [Parameter] public new EventCallback<TValue> ValueChanged { get; set; }

        /// <summary>
        /// Gets or sets an expression that identifies the bound value.
        /// </summary>
        [Parameter] public new Expression<Func<TValue>>? ValueExpression { get; set; }

        /// <summary>
        /// Gets or sets the display name for this field.
        /// <para>This value is used when generating error messages when the input value fails to parse correctly.</para>
        /// </summary>
        [Parameter] public string? DisplayName
        {
            get
            {
                return displayName;
            }

            set
            {
                displayName = value;
            }
        }

        /// <summary>
        /// Gets the associated <see cref="Forms.EditContext"/>.
        /// </summary>
        protected new EditContext EditContext { get; set; } = default!;

        /// <summary>
        /// Gets the <see cref="FieldIdentifier"/> for the bound value.
        /// </summary>
        protected internal new FieldIdentifier FieldIdentifier { get; set; }

        /// <summary>
        /// Gets or sets the current value of the input.
        /// </summary>
        [AllowNull]
        protected new TValue CurrentValue
        {
            [return: MaybeNull]
            get => Value!;
            set
            {
                var hasChanged = !EqualityComparer<TValue>.Default.Equals(value, Value);
                if (hasChanged)
                {
                    Value = value!;
                    _ = ValueChanged.InvokeAsync(Value);
                    EditContext.NotifyFieldChanged(FieldIdentifier);
                }
            }
        }

        /// <summary>
        /// Gets or sets the current value of the input, represented as a string.
        /// </summary>
        //protected string? CurrentValueAsString
        //{
        //    get => FormatValueAsString(CurrentValue);
        //    set
        //    {
        //        _parsingValidationMessages?.Clear();

        //        bool parsingFailed;

        //        if (_nullableUnderlyingType != null && string.IsNullOrEmpty(value))
        //        {
        //            // Assume if it's a nullable type, null/empty inputs should correspond to default(T)
        //            // Then all subclasses get nullable support almost automatically (they just have to
        //            // not reject Nullable<T> based on the type itself).
        //            parsingFailed = false;
        //            CurrentValue = default!;
        //        }
        //        else if (TryParseValueFromString(value, out var parsedValue, out var validationErrorMessage))
        //        {
        //            parsingFailed = false;
        //            CurrentValue = parsedValue!;
        //        }
        //        else
        //        {
        //            parsingFailed = true;

        //            if (_parsingValidationMessages == null)
        //            {
        //                _parsingValidationMessages = new ValidationMessageStore(EditContext);
        //            }

        //            _parsingValidationMessages.Add(FieldIdentifier, validationErrorMessage);

        //            // Since we're not writing to CurrentValue, we'll need to notify about modification from here
        //            EditContext.NotifyFieldChanged(FieldIdentifier);
        //        }

        //        // We can skip the validation notification if we were previously valid and still are
        //        if (parsingFailed || _previousParsingAttemptFailed)
        //        {
        //            EditContext.NotifyValidationStateChanged();
        //            _previousParsingAttemptFailed = parsingFailed;
        //        }
        //    }
        //}
    }
}
