import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import 'rxjs/add/observable/of';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { TransactionModel } from '../model/transaction.model';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';

export interface GetTransactionsResponse {
  transactions: TransactionModel[];
  totalAmount: number;
  totalTransactionCount: number;
}

@Injectable({
  providedIn: 'root'
})
export class TransactionsService {

  // only for mock data
  private restoreTrxArray = [];
  private trxArray = [];
  private transactionId = 'TID12345';
  private transactionIdRecycle = 'TIDRECY';
  private _orderByPipe: OrderByPipe;

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) {
    // mock out the recycle trx
    let t1: any = this.createMockTrx();
    for (let i = 0; i < 13; i++) {
      t1.transactionId = this.transactionIdRecycle + i;
      this.restoreTrxArray.push(new TransactionModel(t1));
    }

    // mock out the trx
    const count = 17;
    t1 = this.createMockTrx();

    this.trxArray = [];
    for (let i = 0; i < count; i++) {
      t1.transactionId = this.transactionId + i;
      t1.amount = 1500 + i;
      this.trxArray.push(new TransactionModel(t1));
    }

    this._orderByPipe = new OrderByPipe();
  }


  /**
   * Gets the transactions for the form type.
   *
   * @param      {String}   formType      The form type of the transaction to get
   * @return     {Observable}             The form being retreived.
   */
  public getFormTransactions(formType: string, page: number, itemsPerPage: number,
      sortColumnName: string, descending: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let params = new HttpParams();
    const url = '/core/get_all_transactions';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('report_id', '1');
    // params = params.append('line_number', '11AI');
    // params = params.append('transaction_type', '15');
    // params = params.append('transaction_type_desc', 'Individual Receipt');
    params = params.append('transaction_id', 'VVBSTFQ9Z78');
    // params = params.append('transaction_date', '2018-10-18');

    // return
    const ob = this._http
     .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions,
          params
        }
      );
    ob.subscribe((res: any) => {
      console.log(res);
    });

    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(this.trxArray, {property: sortColumnName, direction: direction});

    let totalAmount = 0;
    for (const trx of this.trxArray) {
      totalAmount += trx.amount;
    }

    const mockResponse: GetTransactionsResponse = {
      transactions: this.trxArray,
      totalAmount: totalAmount,
      totalTransactionCount: this.trxArray.length
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
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let params = new HttpParams();
    const url = '';

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


    // let t1: any = this.createMockTrx();

    // let trxArray = [];
    // for (let i = 0; i < 8; i++) {
    //   trxArray.push(new TransactionModel(t1));
    // }

    // let mockResponse: GetTransactionsResponse = {
    //   transactions: trxArray,
    //   totalAmount: 0,
    //   totalTransactionCount: 8
    // };

    const mockResponse: GetTransactionsResponse = {
      transactions: this.restoreTrxArray,
      totalAmount: 0,
      totalTransactionCount: this.restoreTrxArray.length
    };
    // console.log(JSON.stringify(mockResponse));
    return Observable.of(mockResponse);
  }


  public restoreTransaction(trx: TransactionModel): Observable<any> {

    const index = this.restoreTrxArray.indexOf(trx);
    if (index !== -1) {
      this.restoreTrxArray.splice(index, 1);
      this.trxArray.push(trx);
    }

    return Observable.of('');
  }


  private createMockTrx() {
    const t1: any = {};
    t1.aggregate = 1000;
    t1.amount = 1500;
    t1.city = 'New York';
    t1.contributorEmployer = 'Exxon';
    t1.contributorOccupation = 'Lawyer';
    const date = new Date('2019-01-01');
    t1.date = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
    t1.memoCode = 'Memo Code';
    t1.memoText = 'The memo text';
    t1.name = 'Mr. John Doe';
    t1.purposeDescription = 'The purpose of this is to...';
    t1.selected = false;
    t1.state = 'New York';
    t1.street = '7th Avenue';
    t1.transactionId = this.transactionId;
    t1.type = 'Individual';
    t1.zip = '22222';

    return t1;
  }
}
