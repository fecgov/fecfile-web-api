import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Custom validator to validate input for floating point numbers.
 *
 * @param      {Object}  control     The control
 * @param      {String}  key         The key
 */
export function floatingPoint(): ValidatorFn {
	return (control: AbstractControl): { [key: string]: any } => {
		const regex: any = new RegExp(/^[0-9.,]+$/g);
		const text: string = control.value;

		if (text) {
			if (text.length >= 1) {
				if (!regex.test(text)) {
					return { nonFloatingPoint: true };
				}
			}
		}

		return null;
	};
}
