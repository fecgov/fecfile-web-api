import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {MessageService} from '../../shared/services/MessageService/message.service';
import {TwoFactorHelperService} from '../service/two-factor-helper/two-factor-helper.service';

@Component({
  selector: 'app-two-factor-login',
  templateUrl: './two-factor-login.component.html',
  styleUrls: ['./two-factor-login.component.scss']
})
export class TwoFactorLoginComponent implements OnInit {

  twoFactInfo: FormGroup;

  constructor(
      private router: Router,
      private _fb: FormBuilder,
      private _messageService: MessageService,
      private _twoFactorService: TwoFactorHelperService,
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

    this.twoFactInfo.markAsTouched();

    // Check requirements
    // for now navigate to two factor code verify screen
    const option = this.twoFactInfo.get('twoFactOption').value;
    this._twoFactorService.requestCode(option).subscribe(res => {
      if (res) {
      }
    });

    if (this.twoFactInfo.valid) {

      this._messageService.sendMessage(
          { action: 'sendSecurityCode', selectedOption: option, entryPoint: 'login' }
          );
        this.router.navigate(['/confirm-2f']).then(r => {
          // handle it
        });
    }
  }

}
