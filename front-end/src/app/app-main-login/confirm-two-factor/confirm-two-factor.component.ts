import { DialogService } from './../../shared/services/DialogService/dialog.service';
import { ManageUserService } from './../../admin/manage-user/service/manage-user-service/manage-user.service';
import { Component, OnInit } from '@angular/core';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import {ConsentModalComponent} from '../consent-modal/consent-modal.component';
import {MessageService} from '../../shared/services/MessageService/message.service';
import {Subscription} from 'rxjs';
import {TwoFactorHelperService} from '../service/two-factor-helper/two-factor-helper.service';
import {AuthService} from '../../shared/services/AuthService/auth.service';
import {PasswordService} from '../../password/service/password.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../../shared/partials/confirm-modal/confirm-modal.component';

@Component({
  selector: 'app-confirm-two-factor',
  templateUrl: './confirm-two-factor.component.html',
  styleUrls: ['./confirm-two-factor.component.scss']
})
export class ConfirmTwoFactorComponent implements OnInit {

  public readonly ACCOUNT_LOCKED_MSG = 'Account is locked. Please try again after 15 mins or call IT support to unlock account.';
  twoFactInfo: FormGroup;
  option: string;

  resendOption: string;
  isValid = true;
  entryPoint: string;
  contactData: any;
  isAccountLocked : boolean;
  private _subscription: Subscription;
  private response: any;
  constructor(
      private router: Router,
      private _fb: FormBuilder,
      private _activatedRoute: ActivatedRoute, 
      private modalService: NgbModal,
      private _messageService: MessageService,
      private _twoFactorService: TwoFactorHelperService,
      private _authService: AuthService,
      private _manageUserService: ManageUserService,
      private _dialogService: DialogService,
      private _passwordService: PasswordService,
  ) {
    this.twoFactInfo = _fb.group({
      securityCode: ['', [Validators.required, Validators.pattern(new RegExp('^[0-9]+$'))]],
    });
  }

  ngOnInit() {
    this._subscription =
        this._messageService
            .getMessage()
            .subscribe(res => {
              if ( res && res.selectedOption !== 'undefined') {
                if (res.action === 'sendSecurityCode') {
                  this.resendOption = res.selectedOption;
                  if (res.selectedOption === 'EMAIL') {
                    this.option = 'Email';
                  } else if (res.selectedOption === 'TEXT' ||
                      res.selectedOption === 'CALL') {
                    this.option = 'Phone Number';
                  }
                  if (res.data) {
                    this.contactData = res.data;
                  }
                  if (res.entryPoint) {
                    this.entryPoint = res.entryPoint;
                  }
                }
              }
            });
    this.isAccountLocked = false;
  }
  onDestroy() {
    this._subscription.unsubscribe();
  }

  back() {
    this.router.navigate(['/login']).then(r => {
      // do nothing
    });
  }

  /**
   * Verify 2 factor security code
   * if allowed ask for consent to login to FEC online system
   * and set the token to be used for further API calls
   * On account lock navigate to login screen
   */
  next() {
    // verify if the code is correct and show consent window
    // if not correct show error to the user
    this.twoFactInfo.markAsTouched();
    if (this.twoFactInfo.valid) {
      const code = this.twoFactInfo.get('securityCode').value;
      if (this.entryPoint === 'login') {
        this._twoFactorService.validateCode(code).subscribe( res => {
          if (res) {

            this.response = res;
            const isAllowed = res['is_allowed'];
            if (isAllowed === true || isAllowed === 'true') {
              this.isValid = isAllowed;
            } else {
              this.isValid = false;
              this.handleAccountLock(res);
              return;
            }
            this.isValid = true;
            this.askConsent();
          } else {
            this.isValid = false;
            return;
          }
        });
      } else if (this.entryPoint === 'registration') {
        this._manageUserService.verifyCode(this.twoFactInfo.value.securityCode).subscribe((resp: any) => {
          if (resp && resp.is_allowed) {
            this.router.navigate(['/createPassword'], {queryParamsHandling: 'merge'});
          } else if ( resp && !resp.is_allowed) {
            this.isValid = false;
          }
        });
      } else if (this.entryPoint === 'reset') {
          this.handleResetPassword(code);
      }
    }
  }
  /**
   * In the case of account lock sign-out the current session nd navigate to HomePage
   * @param response
   * @private
   */
  private handleAccountLock (response: any) {
    this.isAccountLocked = false;
    if (response['msg'] === this.ACCOUNT_LOCKED_MSG) {
      this.isAccountLocked = true;
      setTimeout(() => {
        this._authService.doSignOut();
        this.router.navigate(['/login']).then(r => {
          // do nothing
        });
    }, 5000);
    }
  }

  /**
   * After successful two factor code verification ask for consent
   * If accepted navigate to dashboard else sign-out and navigate to HomePAge
   * @private
   */
  private askConsent() {
    const modalRef = this.modalService.open(ConsentModalComponent, {size: 'lg', centered: true});
    modalRef.result.then((res) => {
      let navUrl = '';
      if (res === 'agree') {
        if (this.response.token) {
          this._authService
              .doSignIn(this.response.token);
        }
          navUrl = '/dashboard';
      } else if (res === 'decline') {
        this._authService.doSignOut();
        navUrl = '[/login]';
      }
      if (this.entryPoint === 'reset' && res === 'agree') {
        this._messageService.sendMessage( { action: 'resetPassword',  entryPoint: 'reset' } );
        this.router.navigate(['/createPassword'], {queryParamsHandling: 'merge'});
      } else {
        this.router.navigate([navUrl]).then(r => {
          // do nothing
        });
      }
    }).catch(e => {
      // do nothing stay on the same page
    });
  }
    resend() {
      if (this.resendOption) {

      this._twoFactorService.requestCode(this.resendOption, this.entryPoint).subscribe((successResp: any) => {
        if (successResp && successResp.is_allowed) {
          this._dialogService.confirm(
            'Security code has been successfully resent',
            ConfirmModalComponent,
            'Code Resent',
            false,
            ModalHeaderClassEnum.successHeader);
        }
      },
      (errorResp: any) => {
        this._dialogService.confirm(
          'There was an issue resending the code. Please try again.',
          ConfirmModalComponent,
          'Error Occured',
          false,
          ModalHeaderClassEnum.errorHeader);
        }
      );
    }
  }

  public selectAnotherType(){
    this.router.navigate(['/register'], {queryParams: {register_token: this._activatedRoute.snapshot.queryParams.register_token}});
  }

  private handleResetPassword(code: string) {
    this._passwordService.verify(code).subscribe(res => {
      if (res) {
        if (res['is_allowed'] === true) {
          this.isValid = true;
          this.response = res;
          this.askConsent();
        } else {
          this.isValid = false;
        }
      }
    });
  }
}
