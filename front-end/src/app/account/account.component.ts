import { Component, EventEmitter, OnInit, Output, Input } from '@angular/core';
import { IAccount } from './account';
import { AccountService } from './account.service';

@Component({
  selector: 'app-account',
  templateUrl: './account.component.html',
  styleUrls: ['./account.component.scss'],
  providers:[AccountService]
})

export class AccountComponent implements OnInit {
  accounts: IAccount;
  
  constructor(private _accountService:AccountService){ 
  }
    
  ngOnInit() {
    console.log("accessing service call...");
    this._accountService.getAccounts()
      .subscribe(res => this.accounts = <IAccount> res);
    console.log(this.accounts)
  }
}
