import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import 'rxjs/add/observable/of';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { TransactionModel } from '../model/transaction.model';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { FilterPipe } from 'src/app/shared/pipes/filter/filter.pipe';

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
  private mockRestoreTrxArray = [];
  private mockTrxArray = [];
  private mockRecycleBinArray = [];
  private mockTransactionId = 'TID12345';
  private mockTransactionIdRecycle = 'TIDRECY';
  // only for mock data - end

  // May only be needed for mocking server
  private _orderByPipe: OrderByPipe;
  private _filterPipe: FilterPipe;

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) {
    // mock out the recycle trx
    for (let i = 0; i < 13; i++) {
      const t1: any = this.createMockTrx();
      t1.transaction_id = this.mockTransactionIdRecycle + i;
      this.mockRestoreTrxArray.push(t1);
    }

    // mock out the trx
    // const count = 17;
    // t1 = this.createMockTrx();

    // this.mockTrxArray = [];
    // for (let i = 0; i < count; i++) {
    //   t1.transactionId = this.transactionId + i;
    //   t1.amount = 1500 + i;
    //   this.mockTrxArray.push(new TransactionModel(t1));
    // }

    this._orderByPipe = new OrderByPipe();
    this._filterPipe = new FilterPipe();
  }


  /**
   * Gets the transactions for the form type.
   *
   * @param      {String}   formType      The form type of the transaction to get
   * @return     {Observable}             The form being retreived.
   */
  public getFormTransactions(
      formType: string,
      page: number,
      itemsPerPage: number,
      sortColumnName: string,
      descending: boolean,
      filter: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let params = new HttpParams();
    const url = '/core/get_all_transactions';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // TODO these will be used for filtering
    // These are not yet defined in API
    // params = params.append('page', page);
    // params = params.append('itemsPerPage', itemsPerPage);
    // params = params.append('sortColumnName', sortColumnName);
    // params = params.append('descending', descending);
    // params = params.append('search', filter.search);

    // These are defined in API
    // params = params.append('report_id', '1');
    // params = params.append('line_number', '11AI');
    // params = params.append('transaction_type', '15');
    // params = params.append('transaction_type_desc', 'Individual Receipt');
    // params = params.append('transaction_id', 'VVBSTFQ9Z78');
    // params = params.append('transaction_date', '2018-10-18');

    return this._http
    .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions,
          params
        }
      );
  }


  /**
   * Map server fields from the response to the model.
   */
  public mapFromServerFields(serverData: any) {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }
    const modelArray = [];
    for (const row of serverData) {
      const model = new TransactionModel({});
      model.type = row.transaction_type_desc;
      model.transactionId = row.transaction_id;
      model.name = row.name;
      model.street = row.street_1 + (row.street_2 ? ' ' + row.street_2 : '');
      model.city = row.city;
      model.state = row.state;
      model.zip = row.zip_code;
      model.date = row.transaction_date;
      model.amount = row.transaction_amount;
      model.aggregate = 0;
      model.purposeDescription = row.purpose_description;
      model.contributorEmployer = row.employer;
      model.contributorOccupation = row.occupation;
      model.memoCode = row.memo_code;
      model.memoText = row.memo_text;
      modelArray.push(model);
    }
    return modelArray;
  }


  /**
   * Map front-end model fields to server fields.
   */
  public mapToServerFields(model: TransactionModel) {

    const serverObject: any = {};
    if (!model) {
      return serverObject;
    }

    serverObject.transaction_type_desc = model.type;
    serverObject.transaction_id = model.transactionId;
    serverObject.name =  model.name;
    serverObject.street_1 = model.street;
    serverObject.city = model.city;
    serverObject.state = model.state;
    serverObject.zip_code = model.zip;
    serverObject.transaction_date = model.date;
    serverObject.transaction_amount = model.amount;
    serverObject.aggregate = model.aggregate;
    serverObject.purpose_description = model.purposeDescription;
    serverObject.employer = model.contributorEmployer;
    serverObject.occupation = model.contributorOccupation;
    serverObject.memo_code = model.memoCode;
    serverObject.memo_text = model.memoText;

    return serverObject;
  }

  // TODO remove once server is ready and mock data is no longer needed
  public mockApplyRestoredTransaction(response: any) {
    for (const trx of this.mockRecycleBinArray) {
      response.transactions.push(trx);
      response.totalAmount += trx.transaction_amount;
      response.totalTransactionCount++;
    }
  }


  public mockApplyFilters(response: any, filters: any) {

    if (!filters) {
      return;
    }
    if (!response.transactions) {
      return;
    }

    let isFilter = false;
    if (filters.search) {
      if (response.transactions.length > 0) {
        isFilter = true;
        const fields = ['name', 'zip_code', 'transaction_id'];
        const filtered = this._filterPipe.transform(response.transactions, fields, filters.search);
        response.transactions = filtered;
      }
    }

    if (filters.filterStates) {
      if (filters.filterStates.length > 0) {
        isFilter = true;
        const fields = ['state'];
        let filteredStateArray = [];
        for (const state of filters.filterStates) {
          const filtered = this._filterPipe.transform(response.transactions, fields, state);
          filteredStateArray = filteredStateArray.concat(filtered);
        }
        response.transactions = filteredStateArray;
      }
    }

    if (filters.filterCategories) {
      if (filters.filterCategories.length > 0) {
        isFilter = true;
        const fields = ['transaction_type_desc'];
        let filteredCategoryArray = [];
        for (const category of filters.filterCategories) {
          const filtered = this._filterPipe.transform(response.transactions, fields, category);
          filteredCategoryArray = filteredCategoryArray.concat(filtered);
        }
        response.transactions = filteredCategoryArray;
      }
    }

    if (filters.filterAmountMin && filters.filterAmountMax) {
      if (filters.filterAmountMin >= 0 && filters.filterAmountMax >= 0 &&
          filters.filterAmountMin <= filters.filterAmountMax) {
        const filteredAmountArray = [];
        for (const trx of response.transactions) {
          if (trx.transaction_amount) {
            if (trx.transaction_amount >= filters.filterAmountMin &&
              trx.transaction_amount <= filters.filterAmountMax) {
                isFilter = true;
                filteredAmountArray.push(trx);
            }
          }
        }
        response.transactions = filteredAmountArray;
      }
    }

    if (isFilter) {
      response.totalAmount = 0;
      response.totalTransactionCount = 0;
      for (const trx of response.transactions) {
        if (!trx.memo_code) {
          response.totalAmount += trx.transaction_amount;
        }
        response.totalTransactionCount++;
      }
    }
  }


  /**
   *
   * @param array
   * @param sortColumnName
   * @param descending
   */
  public sortTransactions(array: any, sortColumnName: string, descending: boolean) {
    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(array, {property: sortColumnName, direction: direction});
    return array;
  }


  /**
   * Gets the transactions for the form.
   *
   * @param      {String}   formType      The form type of the transaction to get
   * @return     {Observable}             An Observable of type `any` containing the transactions
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

    const mockResponse: GetTransactionsResponse = {
      transactions: this.mockRestoreTrxArray,
      totalAmount: 0,
      totalTransactionCount: this.mockRestoreTrxArray.length
    };
    return Observable.of(mockResponse);
  }


  /**
   *
   * @param trx
   */
  public restoreTransaction(trx: TransactionModel): Observable<any> {

    const index = this.mockRestoreTrxArray.findIndex(
      item => item.transaction_id === trx.transactionId);

    if (index !== -1) {
      this.mockRestoreTrxArray.splice(index, 1);
      this.mockRecycleBinArray.push(this.mapToServerFields(trx));
    }

    return Observable.of('');
  }


  private createMockTrx() {
    const t1: any = {};
    t1.aggregate = 1000;
    t1.transaction_amount = 1500;
    t1.city = 'New York';
    t1.employer = 'Exxon';
    t1.occupation = 'Lawyer';
    const date = new Date('2019-01-01');
    t1.transaction_date = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
    t1.deleted_date = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
    t1.memo_code = 'Memo Code';
    t1.memo_text = 'The memo text';
    t1.name = 'Mr. John Doe';
    t1.purpose_description = 'The purpose of this is to...';
    t1.selected = false;
    t1.state = 'New York';
    t1.street_1 = '7th Avenue';
    t1.transaction_id = this.mockTransactionId;
    t1.transaction_type_desc = 'Individual';
    t1.zip_code = '22222';

    return t1;
  }

}
