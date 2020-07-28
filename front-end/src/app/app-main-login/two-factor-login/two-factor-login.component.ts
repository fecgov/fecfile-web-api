import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';

@Component({
  selector: 'app-two-factor-login',
  templateUrl: './two-factor-login.component.html',
  styleUrls: ['./two-factor-login.component.scss']
})
export class TwoFactorLoginComponent implements OnInit {

  twoFactInfo: FormGroup;

  constructor(
      private router: Router,
      private _fb: FormBuilder
  ) {
    this.twoFactInfo = _fb.group({
      twoFactOption: ['', Validators.required],
    });
  }

  ngOnInit() {
  }

  back() {
    // destroy current session if any and return to login page
    this.router.navigate(['/login']).then(r => {
      // do nothing=
    });
  }

  submit() {
    // TODO: submit the form and do not navigate anywhere
    // Check requirements
    // for now navigate to two factor code verify screen
    // if (this.frmUserInfo.valid) {
    if (true) {
      this.router.navigate(['/confirm-2f']).then(r => {
        // handle it
      });
    } /*else {
      this.frmUserInfo.markAsTouched();
    }*/
  }
  handleOptionChange() {
    // Handle the validator change when option changes
    // remove unwanted validators
  }
}
