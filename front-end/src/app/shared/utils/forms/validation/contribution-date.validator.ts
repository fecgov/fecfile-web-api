import { AbstractControl, ValidatorFn } from '@angular/forms';

/**
 * Custom validator to validate if the contribution date is within a report period.
 *
 * @param      {String}  cvgStartDate The cvgStartDate
 * @param      {String}  cvgEndDate The cvgEndDate
 * @param      {Object}  control     The control
 * @param      {String}  key         The key
 */
export function contributionDate(cvgStartDate: string, cvgEndDate: string): ValidatorFn {
  return (control: AbstractControl): { [key: string]: any } => {
    // TODO make this an angular injectable class and inject the util service so that it can
    // be used in an angular way
    function formatDateToYYYMMDD(date: string): string {
      try {
        const dateArr = date.split('/');
        const month: string = dateArr[0];
        const day: string = dateArr[1];
        const year: string = dateArr[2];

        return `${year}-${month}-${day}`;
      } catch (e) {
        return '';
      }
    }

    const text: string = control.value;

    if (typeof text === 'string') {
      if (text.length >= 1) {
        const date: any = new Date(`${text}T01:00:00`);

        const cvgStartDateYYYYMMDD = formatDateToYYYMMDD(cvgStartDate);
        const cvgEndDateYYYYMMDD = formatDateToYYYMMDD(cvgEndDate);
        const cvgStartDateDate: any = new Date(`${cvgStartDateYYYYMMDD}T01:00:00`);
        const cvgEndDateDate: any = new Date(`${cvgEndDateYYYYMMDD}T01:00:00`);

        if (!(date >= cvgStartDateDate && date <= cvgEndDateDate)) {
          return { contributionDateInvalid: true };
        }
      }
    }

    return null;
  };
}
