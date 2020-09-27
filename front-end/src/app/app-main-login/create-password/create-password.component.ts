import { ApiService } from './../../shared/services/APIService/api.service';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbPanelChangeEvent } from '@ng-bootstrap/ng-bootstrap';
import { CookieService } from 'ngx-cookie-service';
import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { mustMatch } from 'src/app/shared/utils/forms/validation/must-match.validator';
import { ManageUserService } from './../../admin/manage-user/service/manage-user-service/manage-user.service';
import {AuthService} from '../../shared/services/AuthService/auth.service';
import {Subscription} from 'rxjs';
import {PasswordService} from '../../password/service/password.service';
import {ConfirmModalComponent, ModalHeaderClassEnum} from '../../shared/partials/confirm-modal/confirm-modal.component';
import {DialogService} from '../../shared/services/DialogService/dialog.service';

@Component({
  selector: 'app-create-password',
  templateUrl: './create-password.component.html',
  styleUrls: ['./create-password.component.scss']
})
export class CreatePasswordComponent implements OnInit {

  public show = false;
  form: FormGroup;
  passwordAccordionExpanded: boolean = false;
  cmteDetailsAccordionExpanded: boolean = false;
  userEmail: any;
  cmteDetails: any;
  private _subscription: Subscription;
  private landingFrom: string;
  successMessage = 'Password has been reset successfully. Proceed to Login.';
  get password() {
    if (this.form && this.form.get('password')) {
      return this.form.get('password').value;
    }
    return null;
  }

  constructor(
    private router: Router,
    private _fb: FormBuilder,
    private _activatedRoute: ActivatedRoute,
    private _apiService: ApiService,
    private _manageUserService: ManageUserService,
    private _cookieService: CookieService,
    private _messageService: MessageService,
    private _authService: AuthService,
    private _resetPassword: PasswordService,
    private _dialogService: DialogService,
    ) { }

  ngOnInit() {
    this._subscription = this._messageService.getMessage().subscribe(res => {
            if (res && res !== 'undefined') {
              if (res.action === 'resetPassword') {
                this.landingFrom = 'resetPassword';
              } else {
                this.landingFrom = 'cratePassword';
              }
            }
            });
    this.initForm();
    this.initCmteInfo();
    this.userEmail = this._activatedRoute.snapshot.queryParams.email;
  }

  private initCmteInfo() {
    this._apiService.getCommiteeDetailsForUnregisteredUsers().subscribe(res => {
      this.cmteDetails = res;
      const userData = this._authService.getCurrentUser();
      this.userEmail = userData.email;
    });
  }

  public toggleAccordion($event: NgbPanelChangeEvent, acc, accordionType: string) {
    if (accordionType === 'passwordAccordion') {
      if (acc.isExpanded($event.panelId)) {
        this.passwordAccordionExpanded = true;
      }
      else {
        this.passwordAccordionExpanded = false;
      }
    }
    else if (accordionType === 'cmteDetailsAccordion') {
      if (acc.isExpanded($event.panelId)) {
        this.cmteDetailsAccordionExpanded = true;
      }
      else {
        this.cmteDetailsAccordionExpanded = false;
      }
    }
  }



  private initForm() {
    const passwordRegex = '(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[$@$!%*?&])[A-Za-z\\d$@$!%*?&]{8,}';
    this.form = this._fb.group({
      password: new FormControl(null, [Validators.required,
        Validators.pattern(new RegExp(passwordRegex))]),
      confirmPassword: new FormControl(null, [Validators.required]),
    }, { validator: [mustMatch('password', 'confirmPassword')] });
  }

  public showPassword() {
    this.show = !this.show;
  }

  public submit() {
    if (this.landingFrom === 'resetPassword') {
          this.resetPassword();
    } else {
      this._manageUserService.createPassword(this.form.value.password)
          .subscribe((resp: any) => {
            if (resp && resp.password_created) {
              this.router.navigate(['/showPersonalKey']).then(success => {
                this._messageService.sendMessage({action: 'sendPersonalKey', key: resp.personal_key});
              });
            }
          });
    }
  }

  /**
   *  Send the new password to API if success notify user and navigate to login screen on dialog
   * @private
   */
  private resetPassword() {
    this._resetPassword.createPassword(this.form.value.password).subscribe( res => {
      if (res && res['password_reset'] === true) {

        this._dialogService.confirm(this.successMessage, ConfirmModalComponent, 'Success!', false,
            ModalHeaderClassEnum.infoHeaderDark, null).then( resp => {
          this.router.navigate(['/login']);
        });
      }
    });
  }


  public ngOnDestroy(): void {
    this._subscription.unsubscribe();
  }
}
