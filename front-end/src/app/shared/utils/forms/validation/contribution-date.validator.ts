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

		if (typeof reportType === 'object' && reportType !== null) {
			if (reportType.hasOwnProperty('cvgStartDate') && reportType.hasOwnProperty('cvgEndDate')) {
				if (
					typeof reportType.cvgStartDate === 'string' &&
					typeof reportType.cvgEndDate === 'string' &&
					(reportType.cvgStartDate !== null && reportType.cvgEndDate !== null)
				) {
					const cvgStartDate: string = reportType.cvgStartDate;
					const cvgEndDate: string = reportType.cvgEndDate;

					if (typeof text === 'string') {
						if (text.length >= 1) {
							const date: any = new Date(`${text}T01:00:00`);
							const formattedDate: string = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date
								.getDate()
								.toString()
								.padStart(2, '0')}/${date.getFullYear()}`;

							if (!(formattedDate >= cvgStartDate && formattedDate <= cvgEndDate)) {
								return { contributionDateInvalid: true };
							}
						}
					}
				}
			}
		}

		return null;
	};
}
