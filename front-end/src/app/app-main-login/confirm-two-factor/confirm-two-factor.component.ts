import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';

@Component({
  selector: 'app-confirm-two-factor',
  templateUrl: './confirm-two-factor.component.html',
  styleUrls: ['./confirm-two-factor.component.scss']
})
export class ConfirmTwoFactorComponent implements OnInit {

  twoFactInfo: FormGroup;
  option: string = 'text';
  constructor(
      private router: Router,
      private _fb: FormBuilder
  ) {
    this.twoFactInfo = _fb.group({
      twoFactOption: ['', Validators.required],
      securityCode: [''],
    });
  }

  ngOnInit() {
  }

  back() {
    this.router.navigate(['/login']).then(r => {
      // do nothing
    });
  }
  next() {

    if (true) {
      this.router.navigate(['/dashboard']).then(r => {
        // handle it
      });
    } /*else {
      this.frmUserInfo.markAsTouched();
    }*/
  }


}
