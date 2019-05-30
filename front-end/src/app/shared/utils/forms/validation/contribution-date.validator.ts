import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Custom validator to validate if the contribution date is within a report period.
 *
 * @param      {Object}  control     The control
 * @param      {String}  key         The key
 */
export function contributionDate(reportType: any): ValidatorFn {
	return (control: AbstractControl): { [key: string]: any } => {
		const text: string = control.value;
		let isDateBetween: boolean = true;

		if (typeof reportType === 'object') {
			if (
				typeof reportType.cvgStartDate === 'string' &&
				(typeof reportType.cvgStartDate === 'string' && typeof reportType.cvgEndDate === 'string')
			) {
				const cvgStartDate: string = reportType.cvgStartDate;
				const cvgEndDate: string = reportType.cvgEndDate;

				if (typeof text === 'string') {
					if (text.length >= 1) {
					}
				}
			}
		}

		return null;
	};
}
