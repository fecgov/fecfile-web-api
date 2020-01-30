import { AbstractControl, ValidatorFn } from '@angular/forms';
import { Injectable } from '@angular/core';
import { UtilService } from '../../util.service';

@Injectable({
  providedIn: 'root'
})
export class MultiStateValidator {
  constructor(private _utilService: UtilService) {}

  /**
   * Custom validator to minimum states selected
   *
   * @param      {String}  minStatesToBeSelected minimum states to be selected
   */
  public multistateSelection(minStatesToBeSelected:number = 6): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } => {
      const array: any = control.value;
        if (array && array.length < minStatesToBeSelected) {
            return { minStates: true };
          }
          return null;
        }
    };
}
