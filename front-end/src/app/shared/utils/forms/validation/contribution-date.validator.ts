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
				typeof reportType.cvgEndDate === 'string' &&
				(reportType.cvgStartDate !== null && reportType.cvgEndDate !== null)
			) {
				const cvgStartDate: string = reportType.cvgStartDate;
				const cvgEndDate: string = reportType.cvgEndDate;

				if (typeof text === 'string') {
					console.log('typeof text: ', typeof text);
					console.log('text.length: ', text.length);
					if (text.length >= 1) {
						const date: Date = new Date(text);
						const formattedDate: string = `${date
							.getDate()
							.toString()
							.padStart(2, '0')}/${date
							.getMonth()
							.toString()
							.padStart(2, '0') + 1}/${date.getFullYear()}`;
						// console.log('text: ', text);
						// console.log('formattedDate: ', formattedDate);
						// console.log('cvgStartDate: ', cvgStartDate);
						// console.log('cvgEndDate: ', cvgEndDate);
					}
				}
			}
		}

		return null;
	};
}
