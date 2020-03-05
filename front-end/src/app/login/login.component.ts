import { Component, OnInit, NgZone , ChangeDetectionStrategy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import { environment } from '../../environments/environment';
import { MessageService } from '../shared/services/MessageService/message.service';
import { CookieService } from 'ngx-cookie-service';
import { ApiService } from '../shared/services/APIService/api.service';
import { AuthService } from '../shared/services/AuthService/auth.service';
import { SessionService } from '../shared/services/SessionService/session.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {

  public frm: FormGroup;
  public isBusy: boolean = false;
  public hasFailed: boolean = false;
  public committeeIdInputError: boolean = false;
  public passwordInputError: boolean = false;
  public loginEmailInputError: boolean = false;
  public appTitle: string = null;
  public loggedOut: any = '';
  private _subscription: Subscription;
  public titleF: string;
  public titleR: string;
  public show: boolean;

  constructor(
    private _fb: FormBuilder,
    private _ngZone: NgZone,
    private _apiService: ApiService,
    private _authService: AuthService,
    private _router: Router,
    private _route: ActivatedRoute,
    private _cookieService: CookieService,
    private _messageService: MessageService,
    private _sessionService: SessionService
  ) {
    this.frm = _fb.group({
      commiteeId: ['', Validators.required],
      loginPassword: ['', Validators.required],
      emailId: ['', Validators.required]
    });
    this._subscription =
      this._messageService
        .getMessage()
        .subscribe(res => {
          if(typeof res.loggedOut !== 'undefined') {
            this.loggedOut = res;
          }
        });
    this.show = false;
 }

  ngOnInit() {
    this._sessionService.destroy();
    localStorage.clear();
    this.appTitle = environment.appTitle;
    this.titleF = this.appTitle.substring(0, 3);
    this.titleR = this.appTitle.substring(3);
  }

  ngOnDestroy() {
    this._subscription.unsubscribe();
  }

  public getLoggedOut() {
    return this.loggedOut;
  }

  /**
   * Updates the form validation when fields have text entered.
   *
   */
  public updateStatus(): void {
    if (this.frm.get('commiteeId').valid) {
      this.committeeIdInputError = false;
    }

    if (this.frm.get('loginPassword').valid) {
      this.passwordInputError = false;
    }

      if (this.frm.get('emailId').valid) {
          this.loginEmailInputError = false;
      }
  }

  /**
   * Signs a user in once form is filled in and submit button clicked.
   *
   */
  public doSignIn(): void {
    if (this.frm.invalid) {
      this.committeeIdInputError = (this.frm.get('commiteeId').invalid) ? true : false;

      this.passwordInputError = (this.frm.get('loginPassword').invalid) ? true : false;

      this.loginEmailInputError = (this.frm.get('emailId').invalid) ? true : false;
       return;
    }

    this.isBusy = true;
    this.hasFailed = false;

    const committeeId: string = this.frm.get('commiteeId').value;
    const password: string = this.frm.get('loginPassword').value;
    const email: string = this.frm.get('emailId').value;

    this._apiService
      .signIn(email, committeeId, password)
      .subscribe(res => {
        if (res.token) {
          this._authService
              .doSignIn(res.token);

          this._router.navigate(['dashboard']);
        }
      },
      (error) => {
        //console.log('error: ', error);
        this.isBusy = false;
        this.hasFailed = true;
      });
  }

  showPassword() {
    this.show = !this.show;
  }
}
