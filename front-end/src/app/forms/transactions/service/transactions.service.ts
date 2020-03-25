import { DatePipe } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { CookieService } from 'ngx-cookie-service';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { map, share } from 'rxjs/operators';
import { FilterPipe, FilterTypeEnum } from 'src/app/shared/pipes/filter/filter.pipe';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { ZipCodePipe } from 'src/app/shared/pipes/zip-code/zip-code.pipe';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { IndividualReceiptService } from '../../form-3x/individual-receipt/individual-receipt.service';
import { TransactionFilterModel } from '../model/transaction-filter.model';
import { TransactionModel } from '../model/transaction.model';

export interface GetTransactionsResponse {
  transactions: TransactionModel[];
  totalAmount: number;
  totalTransactionCount: number;
  totalPages: number;

  // remove after API is renamed.
  itemsPerPage: number;
  'total pages': number;
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
  private _zipCodePipe: ZipCodePipe;
  private _datePipe: DatePipe;
  private _propertyNameConverterMap: Map<string, string> = new Map([['zip', 'zip_code']]);

  private _filterToColMapping =
    [
      {
        "filterName": "filterAmountMin",
        "relatedCol": "amount"
      },
      {
        "filterName": "filterAmountMax",
        "relatedCol": "amount"
      },
      {
        "filterName": "filterLoanAmountMin",
        "relatedCol": "loanAmount"
      },
      {
        "filterName": "filterLoanAmountMax",
        "relatedCol": "loanAmount"
      },
      {
        "filterName": "filterAggregateAmountMin",
        "relatedCol": "aggregate"
      },
      {
        "filterName": "filterAggregateAmountMax",
        "relatedCol": "aggregate"
      },
      {
        "filterName": "filterLoanClosingBalanceMin",
        "relatedCol": "loanClosingBalance"
      },
      {
        "filterName": "filterLoanClosingBalanceMax",
        "relatedCol": "loanClosingBalance"
      },
      {
        "filterName": "filterDateFrom",
        "relatedCol": "date"
      },
      {
        "filterName": "filterDateTo",
        "relatedCol": "date"
      }, {
        "filterName": "filterDeletedDateFrom",
        "relatedCol": "deletedDate"
      },
      {
        "filterName": "filterDeletedDateTo",
        "relatedCol": "deletedDate"
      },
      {
        "filterName": "filterMemoCode",
        "relatedCol": "deletedDate"
      },
      {
        "filterName": "filterElectionCode",
        "relatedCol": "memoCode"
      }
    ]

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
    private _receiptService: IndividualReceiptService, 
    private _messageService: MessageService
  ) {
    // mock out the recycle trx
    for (let i = 0; i < 13; i++) {
      const t1: any = this.createMockTrx();
      t1.transaction_id = this.mockTransactionIdRecycle + i;
      this.mockRestoreTrxArray.push(t1);
    }

    this._orderByPipe = new OrderByPipe();
    this._filterPipe = new FilterPipe();
    this._zipCodePipe = new ZipCodePipe();
    this._datePipe = new DatePipe('en-US');
  }

  /**
   * Gets the transactions by Report ID.
   *
   * @param formType
   * @param reportId
   * @param page
   * @param itemsPerPage
   * @param sortColumnName
   * @param descending
   * @param filters
   * @return     {Observable}
   */
  public getFormTransactions(
    formType: string,
    reportId: string,
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    filters: any,
    categoryType: string,
    trashed_flag: boolean,
    allTransactionsFlag: boolean
  ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/get_all_transactions';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // const serverSortColumnName = this.mapToSingleServerName(sortColumnName);

    const request: any = {};
    if (!allTransactionsFlag && reportId && reportId !== 'undefined') {
      request.reportid = reportId;
    }

    request.page = page;
    request.itemsPerPage = itemsPerPage;
    request.sortColumnName = sortColumnName;
    request.descending = descending;
    request.category_type = categoryType;
    request.trashed_flag = trashed_flag;

    if (filters) {
      request.filters = filters;
      if (request.filters.keywords) {
        const keywordsEdited = [];
        for (const keyword of request.filters.keywords) {
          // replace ` and " with ' for backend.
          let kw = keyword.replace(/\"/g, `'`);
          kw = kw.replace(/`/g, `'`);
          keywordsEdited.push(kw);
        }
        request.filters.keywords = keywordsEdited;
      } else {
        request.filters.keywords = [];
      }
    } else {
      const emptyFilters: any = {};
      emptyFilters.keywords = [];

      request.filters = emptyFilters;
    }

    //console.log(' Transaction Table request = ', request);
    //console.log(' Transaction Table httpOptions = ', httpOptions);

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
      .pipe(
        map(res => {
          if (res) {
            //console.log('Transaction Table res: ', res);

            return res;
          }
          return false;
        }),
        share()
      );
  }

  /**
   * Get the transactions for the user's Recycling Bin by Report ID.
   * These are transactions "trashed" by the user.
   *
   * @param formType
   * @param reportId
   * @param page
   * @param itemsPerPage
   * @param sortColumnName
   * @param descending
   * @param filters
   * @return     {Observable}
   */
  public getUserDeletedTransactions(
    formType: string,
    reportId: string,
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    filters: TransactionFilterModel,
    categoryType: string
  ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/get_all_trashed_transactions';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.reportid = reportId;
    request.page = page;
    request.itemsPerPage = itemsPerPage;
    request.sortColumnName = sortColumnName;
    request.descending = descending;
    request.category_type = categoryType;

    if (filters) {
      request.filters = filters;
      if (request.filters.keywords) {
        const keywordsEdited = [];
        for (const keyword of request.filters.keywords) {
          // replace ` and " with ' for backend.
          let kw = keyword.replace(/\"/g, `'`);
          kw = kw.replace(/`/g, `'`);
          keywordsEdited.push(kw);
        }
        request.filters.keywords = keywordsEdited;
      } else {
        request.filters.keywords = [];
      }
    } else {
      const emptyFilters: any = {};
      emptyFilters.keywords = [];

      request.filters = emptyFilters;
    }

    // For mock response - remove after API is verified
    // const mockResponse: GetTransactionsResponse = {
    //   transactions: this.mockRestoreTrxArray,
    //   totalAmount: 0,
    //   totalTransactionCount: this.mockRestoreTrxArray.length,

    //   // remove after API is renamed.
    //   itemsPerPage: 5,
    //   'total pages': 0
    // };
    // return Observable.of(mockResponse);

    //console.log(' Transaction Recycle Bin Table request = ', request);
    //console.log(' Transaction Recycle Bin Table httpOptions = ', httpOptions);

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
      .pipe(
        map(res => {
          if (res) {
            //console.log('Transaction Recycle Bin Table res: ', res);

            return res;
          }
          return false;
        })
      );
  }

  /**
   * Map server fields from the response to the model.
   *
   * TODO The API should be changed to pass the property names expected by the front end.
   */
  public mapFromServerFields(serverData: any) {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }
    const modelArray = [];
    for (const row of serverData) {
      const model = new TransactionModel({});
      mapDatabaseRowToModel(model, row);
      if (row.child) {
        const modelChildArray = [];
        for (const childRow of row.child) {
          const childModel = new TransactionModel({});
          mapDatabaseRowToModel(childModel, childRow);
          modelChildArray.push(childModel);
        }
        model.child = modelChildArray;
      }
      modelArray.push(model);
    }
    return modelArray;
  }


  public removeFilters(appliedFilters:any, currentSortableColumns: any, transactionSpecificColumns:any): any[]{
    let filteredList = [];
    for (let filter in appliedFilters){
      //get associatedColumn for any non-null filters
      if(typeof filter === "string" && filter.startsWith('filter')){
        let colObj = this._filterToColMapping.find(element => element.filterName === filter);
        let relatedCol = '';
        if(colObj){
          colObj = colObj[0];
          relatedCol = colObj.relatedCol;
          let matchingResults = transactionSpecificColumns.find(element => element.colName === relatedCol);
          if(matchingResults && matchingResults.length > 0){
            filteredList.push(filter);
          }
        }
      }
    }
    return filteredList;
  }


  /**
   * Map Sched server fields to a TransactionModel.
   */
  public mapFromServerSchedFields(serverData: any) {
    if (!serverData || !Array.isArray(serverData)) {
      return;
    }
    const modelArray = [];
    for (const row of serverData) {
      const model = new TransactionModel({});
      this.mapSchedDatabaseRowToModel(model, row);
      if (row.child) {
        const modelChildArray = [];
        for (const childRow of row.child) {
          const childModel = new TransactionModel({});
          this.mapSchedDatabaseRowToModel(childModel, childRow);
          modelChildArray.push(childModel);
        }
        model.child = modelChildArray;
      }
      modelArray.push(model);
    }
    return modelArray;
  }

  public mapSchedDatabaseRowToModel(model: TransactionModel, row: any) {
    // TODO add full field mapping if needed in the future.
    model.transactionId = row.transaction_id;
    model.reportId = row.report_id;
    model.date = row.contribution_date;
    model.memoCode = row.memo_code;
    model.amount = row.contribution_amount;
    model.aggregate = row.contribution_aggregate;
    model.entityId = row.entity_id;
    model.reportType = row.report_type;
    model.candLastName = row.cand_last_name;
    model.candFirstName = row.cand_first_name;
    model.candMiddleName = row.cand_middle_name;
    model.candPrefix = row.cand_prefix;
    model.candSuffix = row.cand_suffix;
    model.candFECId = row.payee_cmte_id;
    model.benificiaryCandId = row.beneficiary_cand_id;
    model.candOffice = row.cand_office;
    model.candOfficeState = row.cand_office_state;
    model.candOfficeDistrict = row.cand_office_district;
    model.candElectionCode = row.election_code;
    model.candElectionYear = row.cand_election_year;
    model.candElectionOtherDesc = row.election_other_desc;
    model.candSupportOpposeFlag = row.support_oppose_code;

    // sched f core child
    model.coordinatedExpInd = row.coordinated_exp_ind;
    model.designatingCmteId = row.designating_cmte_id;
    model.designatingCmteName = row.designating_cmte_name;
    model.subordinateCmteId = row.subordinate_cmte_id;
    model.subordinateCmteName = row.subordinate_cmte_name;
    model.subordinateCmteStreet_1 = row. subordinate_cmte_street_1;
    model.subordinateCmteStreet_2 = row.subordinate_cmte_street_2;
    model.subordinateCmteCity = row.subordinate_cmte_city;
    model.subordinateCmteState = row.subordinate_cmte_state;
    model.subordinateCmteZip = row.subordinate_cmte_zip;
  }

  /**
   * Map a single field name to its server field name equivalent.
   *
   * TODO Too many places where fields names are referenced when converting
   * from/to server names.  Need to consolidate.
   *
   * TODO The API should be changed to pass the property names expected by the front end.
   */
  public mapToSingleServerName(appFieldName: string) {
    // TODO map field names in constructor
    let name = '';

    // if (appFieldName === 'zip') {
    //   this._propertyNameConverterMap.get(appFieldName);
    // }

    name = appFieldName;
    switch (appFieldName) {
      case 'reportType':
        name = 'report_type';
        break;
      case 'type':
        name = 'transaction_type_desc';
        break;
      case 'entityId':
        name = 'entity_id';
        break;
      case 'transactionTypeIdentifier':
        name = 'transaction_type_identifier';
        break;
      case 'transactionId':
        name = 'transaction_id';
        break;
      case 'apiCall':
        name = 'api_call';
        break;
      case 'street':
        name = 'street_1';
        break;
      case 'street2':
        name = 'street_2';
        break;
      case 'zip':
        name = 'zip_code';
        break;
      case 'date':
        name = 'transaction_date';
        break;
      case 'amount':
        name = 'transaction_amount';
        break;
      case 'aggregate':
        name = 'aggregate_amt';
        break;
      case 'purposeDescription':
        name = 'purpose_description';
        break;
      case 'contributorEmployer':
        name = 'employer';
        break;
      case 'contributorOccupation':
        name = 'occupation';
        break;
      case 'memoCode':
        name = 'memo_code';
        break;
      case 'memoText':
        name = 'memo_text';
        break;
      case 'deletedDate':
        name = 'deleted_date';
        break;
      case 'itemized':
        name = 'itemized';
        break;
      case 'electionCode':
        name = 'election_code';
        break;
      case 'loanAmount':
        name = 'loan_amount';
        break;
      case 'loanBalance':
        name = 'loan_balance';
        break;
      case 'loanBeginningBalance':
      case 'debtBeginningBalance':
        name = 'loan_beginning_balance';
        break;
      case 'loanClosingBalance':
        name = 'loan_closing_balance';
        break;
      case 'loanDueDate':
        name = 'loan_due_date';
        break;
      case 'loanIncurredAmt':
        name = 'loan_incurred_amt';
        break;
      case 'loanIncurredDate':
        name = 'loan_incurred_date';
        break;
      case 'loanPaymentAmt':
        name = 'loan_payment_amt';
        break;
      case 'loanPaymentToDate':
        name = 'loan_payment_to_date';
        break;
      default:
    }
    return name ? name : '';
  }

  /**
   * Map front-end model fields to server fields.
   *
   * TODO The API should be changed to pass the property names expected by the front end.
   */
  public mapToServerFields(model: TransactionModel) {
    const serverObject: any = {};
    if (!model) {
      return serverObject;
    }
    serverObject.report_type = model.reportType;
    serverObject.entity_id = model.entityId;
    serverObject.transaction_type_desc = model.type;
    serverObject.transaction_type_identifier = model.transactionTypeIdentifier;
    serverObject.api_call = model.apiCall;
    serverObject.transaction_id = model.transactionId;
    serverObject.name = model.name;
    serverObject.street_1 = model.street;
    serverObject.street_2 = model.street2;
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
    serverObject.itemized = model.itemized;

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

  /**
   * Some data from the server is formatted for display in the UI.  Users will search
   * on the reformatted data.  For the search filter to work against the formatted data,
   * the server array must also contain the formatted data.  They will be added later.
   *
   * @param response the server data
   */
  public addUIFileds(response: any) {
    if (!response) {
      return;
    }
    if (!response.transactions) {
      return;
    }
    for (const trx of response.transactions) {
      trx.transaction_amount_ui = `$${trx.transaction_amount}`;
      trx.transaction_date_ui = this._datePipe.transform(trx.transaction_date, 'MM/dd/yyyy');
      trx.deleted_date_ui = this._datePipe.transform(trx.deleted_date, 'MM/dd/yyyy');
      trx.zip_code_ui = this._zipCodePipe.transform(trx.zip_code);
    }
  }

  /**
   * This method handles filtering the transactions array and will be replaced
   * by a backend API.
   */
  public mockApplyFilters(response: any, filters: TransactionFilterModel) {
    if (!response.transactions) {
      return;
    }

    if (!filters) {
      return;
    }

    let isFilter = false;

    if (filters.keywords) {
      if (response.transactions.length > 0 && filters.keywords.length > 0) {
        isFilter = true;

        const fields = [
          'city',
          'employer',
          'occupation',
          'memo_code',
          'memo_text',
          'name',
          'purpose_description',
          'state',
          'street_1',
          'transaction_id',
          'transaction_type_desc',
          'aggregate',
          'transaction_amount_ui',
          'transaction_date_ui',
          'deleted_date_ui',
          'zip_code_ui',
          'itemized',
          'election_code',
          'election_year',
          ''
        ];

        for (let keyword of filters.keywords) {
          let filterType = FilterTypeEnum.contains;
          keyword = keyword.trim();
          if (
            (keyword.startsWith('"') && keyword.endsWith('"')) ||
            (keyword.startsWith(`'`) && keyword.endsWith(`'`))
          ) {
            filterType = FilterTypeEnum.exact;
            keyword = keyword.valueOf().substring(1, keyword.length - 1);
          }
          const filtered = this._filterPipe.transform(response.transactions, fields, keyword, filterType);
          response.transactions = filtered;
        }
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

    if (filters.filterAmountMin !== null && filters.filterAmountMax !== null) {
      isFilter = true;
      if (
        filters.filterAmountMin >= 0 &&
        filters.filterAmountMax >= 0 &&
        filters.filterAmountMin <= filters.filterAmountMax
      ) {
        const filteredAmountArray = [];
        for (const trx of response.transactions) {
          if (trx.transaction_amount) {
            if (
              trx.transaction_amount >= filters.filterAmountMin &&
              trx.transaction_amount <= filters.filterAmountMax
            ) {
              filteredAmountArray.push(trx);
            }
          }
        }
        response.transactions = filteredAmountArray;
      }
    }

    if (filters.filterDateFrom && filters.filterDateTo) {
      const filterDateFromDate = new Date(filters.filterDateFrom);
      const filterDateToDate = new Date(filters.filterDateTo);
      const filteredDateArray = [];
      for (const trx of response.transactions) {
        if (trx.transaction_date) {
          const trxDate = new Date(trx.transaction_date);
          if (trxDate >= filterDateFromDate && trxDate <= filterDateToDate) {
            isFilter = true;
            filteredDateArray.push(trx);
          }
        }
      }
      response.transactions = filteredDateArray;
    }

    if (filters.filterMemoCode === true) {
      isFilter = true;
      const filteredMemoCodeArray = [];
      for (const trx of response.transactions) {
        if (trx.memo_code) {
          if (trx.memo_code.length > 0) {
            filteredMemoCodeArray.push(trx);
          }
        }
      }
      response.transactions = filteredMemoCodeArray;
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

    if (filters.filterItemizations) {
      if (filters.filterItemizations.length > 0) {
        isFilter = true;
        const fields = ['itemized'];
        let filteredItemizationArray = [];
        for (const itemization of filters.filterItemizations) {
          const filtered = this._filterPipe.transform(response.transactions, fields, itemization);
          filteredItemizationArray = filteredItemizationArray.concat(filtered);
        }
        response.transactions = filteredItemizationArray;
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
    this._orderByPipe.transform(array, { property: sortColumnName, direction: direction });
    return array;
  }

  // /**
  //  * Restore the transaction from the Recyling Bin back to the Transactions Table.
  //  *
  //  * @param trx the transaction to restore
  //  */
  // public restoreTransaction(trx: TransactionModel): Observable<any> {

  //   // mocking the server API until it is ready.

  //   const index = this.mockRestoreTrxArray.findIndex(
  //     item => item.transaction_id === trx.transactionId);

  //   if (index !== -1) {
  //     this.mockRestoreTrxArray.splice(index, 1);
  //     this.mockRecycleBinArray.push(this.mapToServerFields(trx));
  //   }

  //   return Observable.of('');
  // }

  /**
   * Delete transactions from the Recyling Bin.
   *
   * @param transactions the transactions to delete
   */
  public deleteRecycleBinTransaction(transactions: Array<TransactionModel>): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/delete_trashed_transactions';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    const actions = [];
    for (const trx of transactions) {
      actions.push({
        transaction_id: trx.transactionId
      });
    }
    request.actions = actions;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
      .pipe(
        map(res => {
          return false;
        })
      );
  }

  /**
   * Get US States.
   *
   * TODO replace with the appropriate API call when it is available.
   */
  public getStates(formType: string, transactionType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/core/get_dynamic_forms_fields';
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', `F${formType}`);
    params = params.append('transaction_type', transactionType);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions,
      params
    });
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
    const deletedDate = new Date('2019-03-15');
    t1.deleted_date = deletedDate.getFullYear() + '-' + (deletedDate.getMonth() + 1) + '-' + deletedDate.getDate();
    t1.memo_code = 'Memo Code';
    t1.memo_text = 'The memo text';
    t1.name = 'Mr. John Doe';
    t1.purpose_description = 'The purpose of this is to...';
    t1.selected = false;
    t1.state = 'NY';
    t1.street_1 = '7th Avenue';
    t1.transaction_id = this.mockTransactionId;
    t1.transaction_type_desc = 'Individual';
    t1.zip_code = '22222';

    return t1;
  }

  public getItemizations(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/core/get_ItemizationIndicators';
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  /**
   * Trash or restore tranactions to/from the Recycling Bin.
   *
   * @param formType the form type for this report
   * @param action the action to be applied to the transactions (e.g. trash, restore)
   * @param reportId the unique identifier for the Report
   * @param transactions the transactions to trash or restore
   */
  public trashOrRestoreTransactions(
    formType: string,
    action: string,
    reportId: string,
    transactions: Array<TransactionModel>
  ) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/trash_restore_transactions';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    const actions = [];
    for (const trx of transactions) {
      actions.push({
        action: action,
        report_id: trx.reportId && trx.reportId !== 'undefined'? trx.reportId :reportId, 
        transaction_id: trx.transactionId
      });
    }
    request.actions = actions;

    return this._http
      .put(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
      .pipe(
        map(res => {
          if (res) {
            //console.log('Trash Restore response: ', res);
            // refresh the left summary menu
            this._receiptService.getSchedule(formType, { report_id: reportId }).subscribe(resp => {
              const message: any = {
                formType: formType,
                totals: resp
              };
              this._messageService.sendMessage(message);
            });

            return res;
          }
          return false;
        })
      );
  }

  public cloneTransaction(transactionId: string) {

    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/clone_a_transaction';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
      .post(`${environment.apiUrl}${url}`, { transaction_id: transactionId }, {
        headers: httpOptions
      })
      .pipe(
        map(res => {
          if (res) {
            return res;
          }
          return false;
        })
      );
  }
}
function mapDatabaseRowToModel(model: TransactionModel, row: any) {
  model.reportId = row.report_id;
  model.reportType = row.report_type;
  model.formType = row.form_type;
  model.type = row.transaction_type_desc;
  model.scheduleType = row.schedule;
  model.entityId = row.entity_id;
  model.entityType = row.entity_type;
  model.transactionTypeIdentifier = row.transaction_type_identifier;
  model.apiCall = row.api_call;
  model.transactionId = row.transaction_id;
  model.backRefTransactionId = row.back_ref_transaction_id;
  model.name = row.name;
  model.street = row.street_1;
  model.street2 = row.street_2;
  model.city = row.city;
  model.state = row.state;
  model.zip = row.zip_code;
  model.date = row.transaction_date;
  model.amount = row.transaction_amount;
  model.aggregate = row.aggregate_amt;
  model.purposeDescription = row.purpose_description;
  model.contributorEmployer = row.employer;
  model.contributorOccupation = row.occupation;
  model.memoCode = row.memo_code;
  model.memoText = row.memo_text;
  model.deletedDate = row.deleteddate ? row.deleteddate : null;
  model.itemized = row.itemized;
  model.reportstatus = row.reportstatus;
  model.electionCode = row.election_code;
  model.electionYear = row.election_year;
  model.loanAmount = row.loan_amount;
  model.loanBalance = row.loan_balance;
  model.loanBeginningBalance = row.loan_beginning_balance;
  model.loanClosingBalance = row.loan_closing_balance;
  model.loanDueDate = row.loan_due_date;
  model.loanIncurredAmt = row.loan_incurred_amt;
  model.loanIncurredDate = row.loan_incurred_date;
  model.loanPaymentAmt = row.loan_payment_amt;
  model.loanPaymentToDate = row.loan_payment_to_date;
  model.iseditable = row.iseditable;
  model.isTrashable = row.istrashable;
  model.isReattribution = row.isReattribution;
  model.isreattributable = row.isreattributable;
  model.isRedesignation = row.isRedesignation;
  model.isredesignatable = row.isredesignatable;
  model.originalAmount = row.original_amount;
  model.aggregation_ind = row.aggregation_ind;
  model.forceitemizable = row.forceitemizable;

}
