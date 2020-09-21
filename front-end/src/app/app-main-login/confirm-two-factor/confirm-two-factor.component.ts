import { ManageUserService } from './../../admin/manage-user/service/manage-user-service/manage-user.service';
import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import {ConsentModalComponent} from '../consent-modal/consent-modal.component';
import {MessageService} from '../../shared/services/MessageService/message.service';
import {Subscription} from 'rxjs';

@Component({
  selector: 'app-confirm-two-factor',
  templateUrl: './confirm-two-factor.component.html',
  styleUrls: ['./confirm-two-factor.component.scss']
})
export class ConfirmTwoFactorComponent implements OnInit {


  twoFactInfo: FormGroup;
  option: string;
  entryPoint: string;
  contactData: any; 
  private _subscription: Subscription;

  constructor(
      private router: Router,
      private _fb: FormBuilder,
      private modalService: NgbModal,
      private _messageService: MessageService,
      private _manageUserService: ManageUserService
  ) {
    this.twoFactInfo = _fb.group({
      securityCode: ['', Validators.required],
    });
  }

  ngOnInit() {
    this._subscription =
        this._messageService
            .getMessage()
            .subscribe(res => {
              if (res && res.action === 'sendSecurityCode' && res.selectedOption !== 'undefined') {
                if (res.selectedOption === 'email') {
                  this.option = 'email';
                } else if (res.selectedOption.startsWith('phone')) {
                  this.option = 'phone number';
                }

                if(res.data){
                  this.contactData = res.data;
                }
                if(res.entryPoint){
                  this.entryPoint = res.entryPoint;
                }
              }
            });
  }
  onDestroy() {
    this._subscription.unsubscribe();
  }

  back() {
    this.router.navigate(['/login']).then(r => {
      // do nothing
    });
  }
  next() {
    // verify if the code is correct and show consent window
    // if not correct show error to the user
    this.twoFactInfo.markAsTouched();
    if (this.twoFactInfo.valid) {
      if(this.entryPoint === 'login'){
        const modalRef = this.modalService.open(ConsentModalComponent, {size: 'lg', centered: true});
        modalRef.result.then((res) => {
          let navUrl = '';
          if (res === 'agree') {
            navUrl = '/dashboard';
          } else if (res === 'decline') {
            navUrl = '[/login]';
          }
          this.router.navigate([navUrl]).then(r => {
            // do nothing
          });
        }).catch(e => {
          // do nothing stay on the same page
        });
      }
      else if(this.entryPoint === 'registration'){
        this._manageUserService.verifyCode(this.twoFactInfo.value.securityCode).subscribe((resp:any) => {
          if(resp && resp.is_allowed){
            this.router.navigate(['/createPassword']);
          }
        });
      }
    }
  }

    resend() {
      console.log('resending security code');
    }
}
