import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Custom validator to validate input for only amount.
 *
 * @param      {Object}  control     The control
 * @param      {String}  key         The key
 */
export function validateAmount(): ValidatorFn {
    let maxlength = 12;
    let decimal_number = 2
	return (control: AbstractControl): { [key: string]: any } => {
        //const regex: any = new RegExp(/^(?=[0-9.]{1,${maxlength}}$)[0-9]+(?:\.[0-9]{0,${decimal_number}})?$/);
        
        const regex: any = new RegExp(/^\d{0,10}(\.\d{0,2})?$/);
        let text: string = control.value;
        if (text) {
			if (text.length >= 1) {
                text = text.replace(/,/g, ``);
				if (!regex.test(text)) {
					return { nonValidAmount: true };
				}
			}
		}

		return null;
	};
}
