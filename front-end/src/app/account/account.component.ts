// import { Http } from '@angular/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { environment } from '../../environments/environment';
import { CookieService } from 'ngx-cookie-service';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { SessionService } from '../shared/services/SessionService/session.service';
import { ApiService } from '../shared/services/APIService/api.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { FormsComponent } from '../forms/forms.component';
import { DOCUMENT } from '@angular/common';
import { IAccount } from './account';
import { AccountService } from './account.service';

@Component({
  selector: 'app-account',
  templateUrl: './account.component.html',
  styleUrls: ['./account.component.scss'],
  providers: [AccountService]
})

export class AccountComponent implements OnInit {
  accounts: IAccount;
  public showSideBar: boolean = true;
  public showLegalDisclaimer: boolean = false;
  public levin_accounts: any[] = [];
  // = [
  //   {

  //     "levin_account_id": 777,
  //     "levin_account_name": "levin_acct2"
  //   },
  //   {
  //     "levin_account_id": 2,
  //     "levin_account_name": "qqss_tst1"
  //   },
  //   {
  //     "levin_account_id": 3,
  //     "levin_account_name": "qqss_tst22"
  //   }
  // ];

  constructor(
    private _accountService: AccountService,
    private _sessionService: SessionService,
    private _apiService: ApiService,
    private _modalService: NgbModal,
    private _http: HttpClient,
    private _cookieService: CookieService,
    // private _http: Http,
    //private document: Document
  ) {
    // this.levin_accounts = this.getLevinAccounts().subscribe(
    //   response => {

    //   }
    // );
    this.getLevinAccounts().subscribe(res => {
      console.log(res);
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
    // console.log("accessing service call...");
    this._accountService.getAccounts()
      .subscribe(res => this.accounts = <IAccount>res);
    // this.getLevinAccounts().subscribe(res => this.levin_accounts = res.json());
    // console.log(this.accounts)
  }

  goToForms1() {
    window.open('https://webforms.fec.gov/webforms/form1/index.htm', '_blank');
  }


  // TODO: later on to refactor to move http service to a dedicated service module

  saveLevinAccount(levin_name: HTMLInputElement) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/levin_accounts`;
    // const data: any = JSON.stringify(receipt);
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    console.log('levin url:' + url);
    let levin_acct = { "levin_account_name": levin_name.value }
    this._http.post(url, JSON.stringify(levin_acct), {
      headers: httpOptions
    }).subscribe(
      res => {
        console.log(res);
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
    console.log('levin url:' + url);
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
