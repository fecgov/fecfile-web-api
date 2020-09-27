import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {TwoFactorHelperService} from '../../app-main-login/service/two-factor-helper/two-factor-helper.service';
import {MessageService} from '../../shared/services/MessageService/message.service';

@Component({
  selector: 'app-reset-selector',
  templateUrl: './reset-selector.component.html',
  styleUrls: ['./reset-selector.component.scss']
})
export class ResetSelectorComponent implements OnInit {
  frmUserInfo: FormGroup;

  constructor(
      private router: Router,
      private _fb: FormBuilder,
      private twoFactorHelper: TwoFactorHelperService,
      private _messageService: MessageService,
  ) {
    this.frmUserInfo = _fb.group({
      resetOption: ['', Validators.required],
    });
  }

  ngOnInit() {
  }

  back() {
    this.router.navigate(['/reset-password']).then(r => {
      // do nothing
    });
  }

  clearForm() {
    this.frmUserInfo.get('resetOption').reset();
    this.frmUserInfo.markAsPristine();
  }

  submit() {
      this.frmUserInfo.markAsTouched();
     if (this.frmUserInfo.valid) {
       const option = this.frmUserInfo.get('resetOption').value;
       const callFrom = 'reset';
       this.twoFactorHelper.requestCode(option, callFrom).subscribe(response => {
         if (response && response['is_allowed'] === true) {
           this._messageService.sendMessage(
               { action: 'sendSecurityCode', selectedOption: option, entryPoint: 'reset' }
           );
           this.router.navigate(['/confirm-2f']).then(r => {
             // handle it
           });
         }
       });
     }
  }
}
