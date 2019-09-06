import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Custom validator to validate input for only amount.
 * Currently it will validate for {12,2} format
 * we can make it dynamic so that it will validate for any amount formats  
 *
 */
export function validateAmount(): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } => {
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