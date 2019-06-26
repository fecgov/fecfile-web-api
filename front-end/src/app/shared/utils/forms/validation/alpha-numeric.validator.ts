import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Custom validator to validate input for only alphanumeric characters.
 *
 * @param      {Object}  control     The control
 * @param      {String}  key         The key
 */
export function alphaNumeric(): ValidatorFn {
	return (control: AbstractControl): { [key: string]: any } => {
		const regex: any = new RegExp(/^[a-zA-Z0-9\s]*$/);
		const text: string = control.value;

		if (text) {
			if (text.length >= 1) {
				if (!regex.test(text)) {
					return { nonAlphaNumeric: true };
				}
			}
		}

		return null;
	};
}
