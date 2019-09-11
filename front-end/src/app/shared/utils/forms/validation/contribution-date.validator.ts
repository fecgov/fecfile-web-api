import { AbstractControl, ValidatorFn } from '@angular/forms';
import { Injectable } from '@angular/core';
import { UtilService } from '../../util.service';

@Injectable({
  providedIn: 'root'
})
export class ContributionDateValidator {
  constructor(private _utilService: UtilService) {}

  /**
   * Custom validator to validate if the contribution date is within a report period.
   *
   * @param      {String}  cvgStartDate The cvgStartDate
   * @param      {String}  cvgEndDate The cvgEndDate
   * @param      {Object}  control     The control
   * @param      {String}  key         The key
   */
  public contributionDate(cvgStartDate: string, cvgEndDate: string): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } => {
      const text: string = control.value;

      if (typeof text === 'string') {
        if (text.length >= 1) {
          const date: any = new Date(`${text}T01:00:00`);

          const cvgStartDateYYYYMMDD = this._utilService.formatDateToYYYYMMDD(cvgStartDate);
          const cvgEndDateYYYYMMDD = this._utilService.formatDateToYYYYMMDD(cvgEndDate);
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
}
