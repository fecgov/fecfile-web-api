import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import 'rxjs/add/observable/of';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { TransactionModel } from '../model/transaction.model';

export interface GetTransactionsResponse {
  transactions: TransactionModel[];
  totalAmount: number;
  totalTransactionCount: number;
}

@Injectable({
  providedIn: 'root'
})
export class TransactionsService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }


  /**
   * Gets the transactions for the form type.
   *
   * @param      {String}   formType      The form type of the transaction to get
   * @return     {Observable}             The form being retreived.
   */
  public getFormTransactions(formType: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let params = new HttpParams();
    let url: string = '';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('formType', formType);

    // return this._http
    //  .get(
    //     `${environment.apiUrl}${url}`,
    //     {
    //       headers: httpOptions,
    //       params
    //     }
    //   );


    let count = 17;
    let t1: any = this.createMockTrx();

    let trxArray = []; 
    for (let i = 0; i < count; i++) {
      trxArray.push(new TransactionModel(t1));  
    }

    let mockResponse: GetTransactionsResponse = {
      transactions: trxArray,
      totalAmount: 99998,
      totalTransactionCount: count
    };

    console.log(JSON.stringify(mockResponse));

    return Observable.of(mockResponse);
  }


  /**
   * Gets the transactions for the form type.
   *
   * @param      {String}   formType      The form type of the transaction to get
   * @return     {Observable}             The form being retreived.
   */
  public getUserDeletedTransactions(formType: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let params = new HttpParams();
    let url: string = '';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('formType', formType);

    // return this._http
    //  .get(
    //     `${environment.apiUrl}${url}`,
    //     {
    //       headers: httpOptions,
    //       params
    //     }
    //   );


    let t1: any = this.createMockTrx();

    let trxArray = []; 
    for (let i = 0; i < 8; i++) {
      trxArray.push(new TransactionModel(t1));  
    }

    let mockResponse: GetTransactionsResponse = {
      transactions: trxArray,
      totalAmount: 0,
      totalTransactionCount: 8
    };

    //console.log(JSON.stringify(mockResponse));

    return Observable.of(mockResponse);
  }

 
  private createMockTrx() {
    let t1: any = {};
    t1.aggregate = 1000;
    t1.amount = 1500;
    t1.city = "New York";
    t1.contributorEmployer = "Exxon";
    t1.contributorOccupation = "Lawyer";
    let date = new Date('2019-01-01');
    t1.date = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
    t1.memoCode = "Memo Code";
    t1.memoText = "The memo text";
    t1.name = "Mr. John Doe";
    t1.purposeDescription = "The purpose of this is to...";
    t1.selected = false;
    t1.state = "New York";
    t1.street = "7th Avenue";
    t1.transactionId = "TID12345";
    t1.type = "Individual";
    t1.zip = "22222";

    return t1;
  }
}
