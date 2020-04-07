import { Injectable } from '@angular/core';
import { FormGroup } from '@angular/forms';

  /**
   * Custom validator to check that two fields match
   *
   * @param      {String}  controlName first fields control name
   * @param      {String}  matchingControlName second fields control name
   */
  export function mustMatch(controlName: string, matchingControlName: string) {
    return (formGroup: FormGroup) => {
        const control = formGroup.controls[controlName];
        const matchingControl = formGroup.controls[matchingControlName];

        if (matchingControl.errors && !matchingControl.errors.mustMatch) {
            // return if another validator has already found an error on the matchingControl
            return;
        }

        // set error on matchingControl if validation fails
        if (control.value && control.value !== matchingControl.value) {
            matchingControl.setErrors({ mustMatch: true });
        } else {
            matchingControl.setErrors(null);
        }
    }
  }
