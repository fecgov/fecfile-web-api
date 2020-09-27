import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {PasswordService} from '../service/password.service';
import {AuthService} from '../../shared/services/AuthService/auth.service';

@Component({
  selector: 'app-user-info',
  templateUrl: './user-info.component.html',
  styleUrls: ['./user-info.component.scss']
})
export class UserInfoComponent implements OnInit {
    frmUserInfo: FormGroup;

  constructor(
      private router: Router,
      private _fb: FormBuilder,
      private passwordSrv: PasswordService,
      private _authService: AuthService,
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
      const committeeId = this.frmUserInfo.get('committeeID').value;
      const email = this.frmUserInfo.get('email').value;

      this.passwordSrv.authenticate(committeeId, email).subscribe(res => {
        if (res) {
          if (res['is_allowed'] && res['is_allowed'] === true) {
            if (res['token']) {
              this._authService
                  .doSignIn(res['token']);
            }
            this.router.navigate(['/reset-selector']).then(r => {
              // handle it
            });
          } else {
            // TODO: check how to handle errors
            // Do nothing
          }
        }
      });
    } else {
      this.frmUserInfo.markAsTouched();
    }
  }
}
