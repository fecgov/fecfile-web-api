import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Custom validator to validate length of HTML text.
 *
 * @param      {Int}  charLength  The character length
 * @param      {Object}  control     The control
 * @param      {String}  key         The key
 */
export function htmlLength(charLength: number): ValidatorFn {
	return (control: AbstractControl): { [key: string]: any } => {
		const regex: any = /((<(\/?|\!?)\w+>)|(<\w+.*?\w="(.*?)")>|(<\w*.*\/>))/gm;
		let text: string = control.value.replace(regex, '');

		text = text.replace(/(&nbsp;)/g, ' ');

		if (text.length > charLength) {
			return { requiredLength: charLength, actualLength: text.length };
		}

		return null;
	};
}
