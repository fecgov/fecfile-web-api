import {AbstractControl, ValidationErrors, ValidatorFn} from '@angular/forms';

// https://github.com/angular/angular/blob/master/packages/forms/src/validators.ts
function isEmptyInputValue(value: any): boolean {
    // we don't check for string here so it also works with arrays
    return value == null || value.length === 0;
}

function hasValidLength(value: any): boolean {
    // non-strict comparison is intentional, to check for both `null` and `undefined` values
    return value != null && typeof value.length === 'number';
}

function removeCommas(str: string): string {
    return str.toString().replace(new RegExp(',', 'g'), '');
}

export class CustomValidator {
   static noBlankSpaces(control: AbstractControl) {
        if (control && control.value && !control.value.replace(/\s/g, '').length) {
            control.setValue('');
            return {required: true};
        } else {
            return null;
        }
    }

    /**
     * Validator that requires controls to have a value less than a number.
     * Angular max validator modified to validate values containing commas
     */
    static maxAmount(max: number): ValidatorFn {
        return (control: AbstractControl): ValidationErrors | null => {
            if (isEmptyInputValue(control.value) || isEmptyInputValue(max)) {
                return null;  // don't validate empty values to allow optional controls
            }
            const value = parseFloat(removeCommas(control.value));
            // Controls with NaN values after parsing should be treated as not having a
            // maximum, per the HTML forms spec: https://www.w3.org/TR/html5/forms.html#attr-input-max
            return !isNaN(value) && value > max ? {'max': {'max': max, 'actual': control.value}} : null;
        };
    }
}
