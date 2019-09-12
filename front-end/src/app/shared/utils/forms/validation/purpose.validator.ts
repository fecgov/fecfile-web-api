import { AbstractControl, ValidatorFn } from '@angular/forms';
export const IN_KIND = 'in-kind #';

/**
 * Validate a field is required when In-kind# is the prefix.
 *
 * @param fieldName the field to invalidate if validation fails
 * @param prefix prefix for the purpose
 */
export function validatePurposeInKindRequired(fieldName: string, prefix: string): ValidatorFn {
  return (control: AbstractControl): { [key: string]: any } => {
    const purposeVal: string = control.value;

    if (!prefix) {
      return null;
    }
    const invalidObj = {};
    invalidObj[fieldName + 'Invalid'] = true;

    if (purposeVal) {
      const purposeValCompare = purposeVal.trim().toLowerCase();
      const prefixCompare = prefix.trim().toLowerCase();
      if (purposeValCompare === prefixCompare) {
        return invalidObj;
      } if (!purposeValCompare.startsWith(prefixCompare)) {
        return invalidObj;
      }
    } else {
      return invalidObj;
    }
    return null;
  };
}
