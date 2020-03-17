import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Component, OnDestroy, OnInit  } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { CookieService } from 'ngx-cookie-service';
import { Observable, Subject } from 'rxjs';
import 'rxjs/add/observable/of';
import { environment } from '../../environments/environment';
import { ApiService } from '../shared/services/APIService/api.service';
import { SessionService } from '../shared/services/SessionService/session.service';
import { IAccount } from './account';
import { AccountService } from './account.service';

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

  constructor(
    private _accountService: AccountService,
    private _sessionService: SessionService,
    private _apiService: ApiService,
    private _modalService: NgbModal,
    private _http: HttpClient,
    private _cookieService: CookieService,
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


}
