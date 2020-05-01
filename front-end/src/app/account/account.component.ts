import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Component, OnDestroy, OnInit  } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { CookieService } from 'ngx-cookie-service';
import { Observable, Subject, Subscription } from 'rxjs';
import 'rxjs/add/observable/of';
import { environment } from '../../environments/environment';
import { ApiService } from '../shared/services/APIService/api.service';
import { SessionService } from '../shared/services/SessionService/session.service';
import { IAccount } from './account';
import { AccountService } from './account.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import {AuthService} from '../shared/services/AuthService/auth.service';

@Component({
  selector: 'app-account',
  templateUrl: './account.component.html',
  styleUrls: ['./account.component.scss'],
  providers: [AccountService]
})

export class AccountComponent implements OnInit, OnDestroy {
  accounts: IAccount;
  public showSideBar: boolean = true;
  public showLegalDisclaimer: boolean = false;
  public levin_accounts: any[] = [];
  private onDestroy$ = new Subject();

  public levinAction = 'add';
  public levinsSubscription: Subscription;
  public editLevinAccountId: string;

  constructor(
    private _accountService: AccountService,
    private _sessionService: SessionService,
    private _apiService: ApiService,
    private _modalService: NgbModal,
    private _http: HttpClient,
    private _cookieService: CookieService,
    private _dialogService: DialogService,
    public _authService: AuthService,
  ) {
    this.getLevinAccounts().takeUntil(this.onDestroy$).subscribe(res => {
      //console.log(res);
      if (res) {
        this.levin_accounts = res;
      }
    });
  }

  public toggleSideNav(): void {
    if (this.showSideBar) {
      this.showSideBar = false;
    } else if (!this.showSideBar) {
      this.showSideBar = true;
    }
  }

  public open(): void {
    this.showLegalDisclaimer = !this.showLegalDisclaimer;
  }

  ngOnInit() {
    this._accountService.getAccounts().takeUntil(this.onDestroy$)
      .subscribe(res => this.accounts = <IAccount>res);
  }

  goToForms1() {
    window.open('https://webforms.fec.gov/webforms/form1/index.htm', '_blank');
  }

  ngOnDestroy(){
    this.onDestroy$.next(true);
  }


  // TODO: later on to refactor to move http service to a dedicated service module

  saveLevinAccount(levin_name: HTMLInputElement) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/levin_accounts`;
    // const data: any = JSON.stringify(receipt);
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    //console.log('levin url:' + url);
    let levin_acct = { "levin_account_name": levin_name.value }
    this._http.post(url, JSON.stringify(levin_acct), {
      headers: httpOptions
    }).subscribe(
      res => {
        //console.log(res);
        levin_acct['levin_account_id'] = res[0].levin_account_id;
        this.levin_accounts.splice(0, 0, levin_acct);
      });
    // reset levin name field
    levin_name.value = '';

  }

  private getLevinAccounts(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/levin_accounts`;
    // const data: any = JSON.stringify(receipt);
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    //console.log('levin url:' + url);
    return this._http.get(url, {
      headers: httpOptions,
      // params: {
      //   report_id: receipt.report_id
      // }
    });

  }



  // getLevinAccounts(){

  // }

  public editLevinAccount(levin: any) {
    this.levinAction = 'edit';

    (<HTMLInputElement> document.getElementById('levin_acct_name')).value = levin.levin_account_name;
    this.editLevinAccountId = levin.levin_account_id;

    this.levin_accounts = this.levin_accounts.filter(obj => obj.levin_account_id !== levin.levin_account_id);

  }

  public saveEdit(levin_name: HTMLInputElement) {
      const token: string = JSON.parse(this._cookieService.get('user'));
      const url: string = `${environment.apiUrl}/core/levin_accounts`;

      let httpOptions = new HttpHeaders();

      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
      httpOptions = httpOptions.append('Content-Type', 'application/json');

      let levin_acct = {
        "levin_account_id": this.editLevinAccountId,
        "levin_account_name": levin_name.value
      }

      this._http.put(url, JSON.stringify(levin_acct), {
        headers: httpOptions
      }).subscribe(
        res => {
          this.resetToAddLevin();

          this.editLevinAccountId = '';
      });
  }

  public cancelEditLevinAccount() {
    this.resetToAddLevin();
  }

  private resetToAddLevin() {
    this.levinsSubscription = this.getLevinAccounts()
      .subscribe( message => {
        this.levin_accounts = message;
      });
    this.levinAction = 'add';
    (<HTMLInputElement> document.getElementById('levin_acct_name')).value = '';
  }

  public trashLevinAccount(levin: any) {

    this._dialogService
      .confirm('You are about to delete this levin account ' + levin.levin_account_name + '.', ConfirmModalComponent, 'Caution!')
      .then(res => {
        if (res === 'okay') {

          this.trahAction(levin.levin_account_id);

          this.levin_accounts = this.levin_accounts.filter(obj => obj.levin_account_id !== levin.levin_account_id);
          this._dialogService.confirm(
            'Transaction has been successfully deleted. ' + levin.levin_account_name,
            ConfirmModalComponent,
            'Success!',
            false,
            ModalHeaderClassEnum.successHeader
          );

        } else if (res === 'cancel') {
        }
      });
  }

  public trahAction(levin_account_id: string) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/levin_accounts`;

    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    httpOptions = httpOptions.append('Content-Type', 'application/json');

    let params = new HttpParams();
    params = params.append('levin_account_id', levin_account_id);

    this._http.delete(url, {
      params,
      headers: httpOptions
    }).subscribe(
      res => {
        this.resetToAddLevin();
    });
  }

}
