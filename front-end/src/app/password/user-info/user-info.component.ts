import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';

@Component({
  selector: 'app-user-info',
  templateUrl: './user-info.component.html',
  styleUrls: ['./user-info.component.scss']
})
export class UserInfoComponent implements OnInit {
    frmUserInfo: FormGroup;

  constructor(
      private router: Router,
      private _fb: FormBuilder
  ) {
    this.frmUserInfo = _fb.group({
     committeeID: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]]
    });
  }

  ngOnInit() {
  }

  gotoLogin() {
    this.router.navigate(['']).then(r => {
      // do nothing
    });
  }

  clearForm() {
    this.frmUserInfo.reset();
  }

  resetNextPage() {
    if (this.frmUserInfo.valid) {
    this.router.navigate(['/reset-selector']).then(r => {
      // handle it
    });
    } else {
      this.frmUserInfo.markAsTouched();
    }
  }
}
