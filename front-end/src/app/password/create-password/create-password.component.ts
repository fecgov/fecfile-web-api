import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';

@Component({
  selector: 'app-create-password',
  templateUrl: './create-password.component.html',
  styleUrls: ['./create-password.component.scss']
})
export class CreatePasswordComponent implements OnInit {
  static readonly passwordLength = 8;
  frmUserInfo: FormGroup;
  protected userName = '';
  isCollapsed = true;
  isCollapsedC = true;
  public barLabel: string = 'Password strength:';
  protected passwordChanged: string = '';


  constructor(
      private router: Router,
      private _fb: FormBuilder
  ) {
    this.frmUserInfo = _fb.group({
      password: ['', Validators.required],
      confirmPassword: ['', Validators.required],
    });
  }

  ngOnInit() {
  }


  submit() {
  // TODO: remove later

  }

  showPassword(password: string) {

  }

  passwordChange() {
    if (this.frmUserInfo.get('password')) {
      this.passwordChanged = this.frmUserInfo.get('password').value;
    }
  }
}
