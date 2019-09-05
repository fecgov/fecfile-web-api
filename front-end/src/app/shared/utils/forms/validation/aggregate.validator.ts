import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Validate a field is required when aggregate is greater than 200.
 *
 * @param aggregate the aggregate amount to check
 * @param required true if validation should be applied fo the field
 * @param fieldName the field to invalidate if validation fails
 */
export function validateAggregate(aggregate: any, required: boolean, fieldName: string): ValidatorFn {
  return (control: AbstractControl): { [key: string]: any } => {
    if (required) {
      // The employer, occupation, etc value required when aggregate > 200
      const requireFieldVal: string = control.value;

      let aggregateNum = 0;
      if (typeof aggregate === 'string') {
        // default to 0 when no value
        aggregate = aggregate ? aggregate : '0';

        // remove commas
        aggregate = aggregate.replace(/,/g, ``);

        aggregateNum = parseFloat(aggregate);
      } else {
        aggregateNum = aggregate;
      }

      if (!requireFieldVal) {
        if (aggregateNum > 200) {
          const invalidObj = {};
          invalidObj[fieldName + 'Invalid'] = true;
          return invalidObj;
        }
      }
    }
    return null;
  };
}
