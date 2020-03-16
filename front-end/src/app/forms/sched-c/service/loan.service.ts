import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { LoanModel } from '../model/loan.model';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { FilterPipe, FilterTypeEnum } from 'src/app/shared/pipes/filter/filter.pipe';
import { DatePipe } from '@angular/common';
import { ZipCodePipe } from 'src/app/shared/pipes/zip-code/zip-code.pipe';
import { map } from 'rxjs/operators';
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';

export interface GetLoanResponse {
  loans: LoanModel[];
  totalAmount: number;
  totalloansCount: number;
  totalPages: number;

  // remove after API is renamed.
  itemsPerPage: number;
  'total pages': number;
}

// export enum ScheduleActions {
//   add = 'add',
//   edit = 'edit',
// }

@Injectable({
  providedIn: 'root'
})
export class LoanService {

  // only for mock data
  private mockRestoreTrxArray = [];
  private mockTrxArray = [];
  private mockRecycleBinArray = [];
  private mockContactId = 'TID12345';
  private mockContactIdRecycle = 'TIDRECY';
  // only for mock data - end

  // May only be needed for mocking server
  private _orderByPipe: OrderByPipe;
  private _filterPipe: FilterPipe;
  private _zipCodePipe: ZipCodePipe;
  private _datePipe: DatePipe;
  private _propertyNameConverterMap: Map<string, string> = new Map([
    ['zip', 'zip_code'],
  ]);


  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
    private _reportTypeService: ReportTypeService,
  ) {
    // mock out the recycle cnt
    for (let i = 0; i < 13; i++) {
      const t1: any = this.createMockTrx();
      t1.transaction_id = this.mockContactIdRecycle + i;
      this.mockRestoreTrxArray.push(t1);
    }

    this._orderByPipe = new OrderByPipe();
    this._filterPipe = new FilterPipe();
    this._zipCodePipe = new ZipCodePipe();
    this._datePipe = new DatePipe('en-US');
  }

  /**
   * Gets the contacts by Report ID.
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
  public getLoan(message: any = null): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sc/get_outstanding_loans';


    let reportId : string = '';
    if(message && message.reportId && message.reportId !== 'undefined' && message.reportId !== '0'){
      reportId = message.reportId;
    }
    else{
      reportId = this._reportTypeService.getReportIdFromStorage('3X').toString();
    }

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', reportId);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions,
          params
        }
      )
      .pipe(map(res => {
        if (res) {
          //console.log('get_outstanding_loans API res: ', res);

          return res;
        }
        return false;
      }));
  }

  deleteLoan(loan: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sc/schedC';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('transaction_id', loan.transaction_id);

    return this._http.delete(
      `${environment.apiUrl}${url}`,
      {
        params,
        headers: httpOptions
      }
    )
      .pipe(map(res => {
        if (res) {
          //console.log('get_outstanding_loans API res: ', res);

          return res;
        }
        return false;
      }));
  }

  deleteEndorser(endorser: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sc/schedC2';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('transaction_id', endorser.transaction_id);

    return this._http.delete(
      `${environment.apiUrl}${url}`,
      {
        params,
        headers: httpOptions
      }
    )
      .pipe(map(res => {
        if (res) {
          return res;
        }
        return false;
      }));
  }


  /**
  * Gets the endorsers by loan transactionId.
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
  public getEndorsers(loanTransactionId: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sc/get_endorser_summary';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('transaction_id', loanTransactionId);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          params,
          headers: httpOptions
        }
      )
      .pipe(map(res => {
        if (res) {
          return res;
        }
        return false;
      }));

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
      const model = new LoanModel({});
      model.entity_type = row.entity_type;
      model.cmte_id = row.cmte_id;
      model.report_id = row.report_id;
      model.line_number = row.line_number;
      model.transaction_type = row.transaction_type;
      model.transaction_type_identifier = row.transaction_type_identifier;
      model.transaction_id = row.transaction_id;
      model.entity_id = row.entity_id;
      model.name = row.name;
      model.street1 = row.street1;
      model.street2 = row.street2;
      model.city = row.city;
      model.state = row.state;
      model.zip = row.zip;
      model.phoneNumber = row.phoneNumber;
      model.election_code = row.election_code;
      model.election_other_description = row.election_other_description;
      model.loan_amount_original = row.loan_amount_original;
      model.loan_payment_to_date = row.loan_payment_to_date;
      model.loan_balance = row.loan_balance;
      model.loan_incurred_date = row.loan_incurred_date;
      model.loan_due_date = row.loan_due_date;
      model.loan_intrest_rate = row.loan_intrest_rate;
      model.is_loan_secured = row.is_loan_secured;
      model.is_personal_funds = row.is_personal_funds;
      model.lender_cmte_id = row.lender_cmte_id;
      model.lender_cand_id = row.lender_cand_id;
      model.lender_cand_last_name = row.lender_cand_last_name;
      model.lender_cand_first_name = row.lender_cand_first_name;
      model.lender_cand_middle_name = row.lender_cand_middle_name;
      model.lender_cand_prefix = row.lender_cand_prefix;
      model.lender_cand_suffix = row.lender_cand_suffix;
      model.lender_cand_office = row.lender_cand_office;
      model.lender_cand_state = row.lender_cand_state;
      model.lender_cand_district = row.lender_cand_district;
      model.memo_code = row.memo_code;
      model.memo_text = row.memo_text;
      model.delete_ind = row.delete_ind;
      model.child = row.child
      model.payments = row.payments;
      model.hasC1 = row.hasC1;
      model.hasC2 = row.hasC2;
      modelArray.push(model);
    }
    return modelArray;
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
      case 'name':
        name = 'name';
        break;
      case 'entity_name':
        name = 'entity_name';
        break;
      case 'entityType':
        name = 'entityType';
        break;
      case 'id':
        name = 'id';
        break;
      case 'street1':
        name = 'street1';
        break;
      case 'street2':
        name = 'street2';
        break;
      case 'city':
        name = 'city';
        break;
      case 'state':
        name = 'state';
        break;
      case 'zip':
        name = 'zip';
        break;
      case 'employer':
        name = 'employer';
        break;
      case 'occupation':
        name = 'occupation';
        break;
      case 'phoneNumber':
        name = 'phoneNumber';
        break;
      case 'cmte_id':
        name = 'cmte_id';
        break;
      case 'report_id':
        name = 'report_id';
        break;
      case 'line_number':
        name = 'line_number';
        break;
      case 'transaction_type':
        name = 'transaction_type';
        break;
      case 'transaction_type_identifier':
        name = 'transaction_type_identifier';
        break;
      case 'transaction_id':
        name = 'transaction_id';
        break;
      case 'entity_id':
        name = 'entity_id';
        break;
      case 'election_code':
        name = 'election_code';
        break;
      case 'election_other_description':
        name = 'election_other_description';
        break;
      case 'loan_amount_original':
        name = 'loan_amount_original';
        break;
      case 'loan_payment_to_date':
        name = 'loan_payment_to_date';
        break;
      case 'loan_payment_to_date':
        name = 'loan_payment_to_date';
        break;
      case 'loan_balance':
        name = 'loan_balance';
        break;
      case 'loan_incurred_date':
        name = 'loan_incurred_date';
        break;
      case 'loan_due_date':
        name = 'loan_due_date';
        break;
      case 'loan_intrest_rate':
        name = 'loan_intrest_rate';
        break;
      case 'is_loan_secured':
        name = 'is_loan_secured';
        break;
      case 'is_personal_funds':
        name = 'is_personal_funds';
        break;
      case 'lender_cmte_id':
        name = 'lender_cmte_id';
        break;
      case 'lender_cand_id':
        name = 'lender_cand_id';
        break;
      case 'lender_cand_last_name':
        name = 'lender_cand_last_name';
        break;
      case 'lender_cand_first_name':
        name = 'lender_cand_first_name';
        break;
      case 'lender_cand_middle_name':
        name = 'lender_cand_middle_name';
        break;
      case 'lender_cand_prefix':
        name = 'lender_cand_prefix';
        break;
      case 'lender_cand_suffix':
        name = 'lender_cand_suffix';
        break;
      case 'lender_cand_office':
        name = 'lender_cand_office';
        break;
      case 'delete_ind':
        name = 'delete_ind';
        break;
      case 'memo_text':
        name = 'memo_text';
        break;
      case 'memo_code':
        name = 'memo_code';
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
  public mapToServerFields(model: LoanModel) {

    const serverObject: any = {};
    if (!model) {
      return serverObject;
    }

    serverObject.entity_type = model.entity_type;
    serverObject.cmte_id = model.cmte_id;
    serverObject.report_id = model.report_id;
    serverObject.line_number = model.line_number;
    serverObject.transaction_type = model.transaction_type;
    serverObject.transaction_type_identifier = model.transaction_type_identifier;
    serverObject.transaction_id = model.transaction_id;
    serverObject.entity_id = model.entity_id;
    serverObject.name = model.name;
    serverObject.entity_type = model.entity_type;
    serverObject.street1 = model.street1;
    serverObject.street2 = model.street2;
    serverObject.city = model.city;
    serverObject.state = model.state;
    serverObject.zip = model.zip;
    serverObject.phoneNumber = model.phoneNumber;
    serverObject.election_code = model.election_code;
    serverObject.election_other_description = model.election_other_description;
    serverObject.loan_amount_original = model.loan_amount_original;
    serverObject.loan_payment_to_date = model.loan_payment_to_date;
    serverObject.loan_balance = model.loan_balance;
    serverObject.loan_incurred_date = model.loan_incurred_date;
    serverObject.loan_due_date = model.loan_due_date;
    serverObject.loan_intrest_rate = model.loan_intrest_rate;
    serverObject.is_loan_secured = model.is_loan_secured;
    serverObject.is_personal_funds = model.is_personal_funds;
    serverObject.lender_cmte_id = model.lender_cmte_id;
    serverObject.lender_cand_id = model.lender_cand_id;
    serverObject.lender_cand_last_name = model.lender_cand_last_name;
    serverObject.lender_cand_first_name = model.lender_cand_first_name;
    serverObject.lender_cand_middle_name = model.lender_cand_middle_name;
    serverObject.lender_cand_prefix = model.lender_cand_prefix;
    serverObject.lender_cand_suffix = model.lender_cand_suffix;
    serverObject.lender_cand_office = model.lender_cand_office;
    serverObject.lender_cand_state = model.lender_cand_state;
    serverObject.lender_cand_district = model.lender_cand_district;
    serverObject.memo_code = model.memo_code;
    serverObject.memo_text = model.memo_text;
    serverObject.delete_ind = model.delete_ind;
    return serverObject;
  }

  // TODO remove once server is ready and mock data is no longer needed
  public mockApplyRestoredContact(response: any) {
    for (const cnt of this.mockRecycleBinArray) {
      response.contacts.push(cnt);
      response.totalAmount += cnt.transaction_amount;
      response.totalContactCount++;
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
    if (!response.contacts) {
      return;
    }
    for (const cnt of response.contacts) {
      cnt.deleted_date_ui = this._datePipe.transform(cnt.deleteddate, 'MM/dd/yyyy');
    }
  }


  /**
   * This method handles filtering the contacts array and will be replaced
   * by a backend API.
   */
  public mockApplyFilters(response: any) {

    if (!response.contacts) {
      return;
    }
  }

  private getDateMMDDYYYYformat(dateValue: Date): Date {
    var utc = new Date(dateValue.getUTCFullYear(), dateValue.getUTCMonth() + 1, dateValue.getUTCDate());
    utc.setUTCHours(0, 0, 0, 0);
    return utc
  }

  /**
   *
   * @param array
   * @param sortColumnName
   * @param descending
   */
  public sortLoan(array: any, sortColumnName: string, descending: boolean) {
    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(array, { property: sortColumnName, direction: direction });
    return array;
  }

  /**
 *
 * @param array
 * @param sortColumnName
 * @param descending
 */
  public sortEndorser(array: any, sortColumnName: string, descending: boolean) {
    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(array, { property: sortColumnName, direction: direction });
    return array;
  }

  /**
   * Get transaction category types
   * 
   * @param formType
   */
  public getContactCategories(formType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_transaction_categories';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', `F${formType}`);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          params,
          headers: httpOptions
        }
      );
  }

  public getStates(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/core/state';
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  public getTypes(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/core/get_entityTypes';
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
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
    t1.transaction_id = this.mockContactId;
    t1.transaction_type_desc = 'Individual';
    t1.zip_code = '22222';

    return t1;
  }

  /**
 * Trash or restore tranactions to/from the Recycling Bin.
 * 
 * @param action the action to be applied to the contacts (e.g. trash, restore)
 * @param reportId the unique identifier for the Report
 * @param contacts the contacts to trash or restore
 */
  public trashOrRestoreLoan(action: string, contacts: Array<LoanModel>) {
    /*
     const token: string = JSON.parse(this._cookieService.get('user'));
     let httpOptions =  new HttpHeaders();
     const url = '/core/trash_restore_contact';
 
     httpOptions = httpOptions.append('Content-Type', 'application/json');
     httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
 
     const request: any = {};
     const actions = [];
     for (const cnt of contacts) {
       actions.push({
         action: action,
         id: cnt.id
       });
     }
     request.actions = actions;
 
     return this._http
     .put(
       `${environment.apiUrl}${url}`,
       request,
       {
         headers: httpOptions
       }
     )
     .pipe(map(res => {
         if (res) {
           //console.log('Trash Restore response: ', res);
           return res;
         }
         return false;
     }));*/

  }

  /**
   * Gets the saved transaction data for the schedule.
   *
   * @param      {string}  reportId  The report Id
   * @param      {string}  transactionId   The Transaction Id
   * @param      {string}  apiCall   This parameter derives the API call
   */
  public getDataSchedule(reportId: string, transactionId: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/sc/schedC`;
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', reportId);
    if (transactionId) {
      params = params.append('transaction_id', transactionId);
    }

    return this._http.get(url, {
      headers: httpOptions,
      params: params
    });
  }

  /**
   * Gets the schedule after submitted.
   *
   * @param      {string}  formType  The form type
   * @param      {any}     receipt   The receipt
   */
  public getSchedule(formType: string, receipt: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/thirdNavTransactionTypes`;
    const data: any = JSON.stringify(receipt);
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(url, {
      headers: httpOptions,
      params: {
        report_id: receipt.report_id
      }
    });
  }

  /**
  * Saves a schedule.
  *
  * @param      {string}           formType  The form type
  * @param      {ScheduleActions}  scheduleAction  The type of action to save (add, edit)
  */
  public saveSched_C(scheduleAction: ScheduleActions, transactionTypeIdentifier: string, subType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/sc/schedC';
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();
    const loan: any = JSON.parse(localStorage.getItem('LoanObj'));
    const loanByCommFromIndObj: any = {
      api_call: '/sc/schedC',
      line_number: 13,
      //transaction_id:'16G',
      transaction_id: loan.transaction_id,
      back_ref_transaction_id: '',
      back_ref_sched_name: '',
      transaction_type: 'LOAN_FROM_IND',
      transaction_type_identifier: 'LOANS_OWED_BY_CMTE'
    };
    const loanByCommFromBankObj: any = {
      api_call: '/sc/schedC',
      line_number: 13,
      //transaction_id:'16F',
      transaction_id: loan.transaction_id,
      back_ref_transaction_id: '',
      back_ref_sched_name: '',
      transaction_type: 'LOAN_FROM_BANK',
      transaction_type_identifier: 'LOANS_OWED_BY_CMTE'
    };
    const loanToCommObj: any = {
      api_call: '/sc/schedC',
      line_number: 13,
      transaction_id: '',
      back_ref_transaction_id: '',
      back_ref_sched_name: '',
      transaction_type: 'LOAN_TO_COMM',
      transaction_type_identifier: 'LOANS_OWED_TO_CMTE'
    };

    /*const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }*/

    //const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
    const formData: FormData = new FormData();
    let httpOptions = new HttpHeaders();
    let loanhiddenFields: any;
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    //console.log(" saveSched_C transactionTypeIdentifier =", transactionTypeIdentifier)
    //console.log(" saveSched_C subType =", subType)

    for (const [key, value] of Object.entries(loan)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }

    if (transactionTypeIdentifier === 'LOANS_OWED_BY_CMTE') {
      if (subType === 'IND') {
        loanhiddenFields = loanByCommFromIndObj;
      } else if (subType === 'ORG') {
        loanhiddenFields = loanByCommFromBankObj;
      }
    } else if (transactionTypeIdentifier === 'LOANS_OWED_TO_CMTE') {
      loanhiddenFields = loanToCommObj;
    }

    //console.log("loanhiddenFields", loanhiddenFields);

    //Add loan hidden fields
    for (const [key, value] of Object.entries(loanhiddenFields)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }
    //console.log("saveSched_C reportId =", reportId);

    formData.append('report_id', reportId);

    if (scheduleAction === ScheduleActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              //console.log(" saveLoan called res...!", res);
              return res;
            }
            return false;
          })
        );
    } else if (scheduleAction === ScheduleActions.edit) {
      return this._http
        .put(`${environment.apiUrl}${url}`, formData, {
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
    } else {
    }
  }

  public get_sched_c_loan_dynamic_forms_fields(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/get_sched_c_loan_dynamic_forms_fields`;
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(url, {
      headers: httpOptions
    });
  }


  /**
   * Saves a schedule.
   *
   * @param      {string}           formType  The form type
   * @param      {ScheduleActions}  scheduleAction  The type of action to save (add, edit)
   */
  public saveSched_C2(scheduleAction: ScheduleActions, endorserForm: any, hiddenFields: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/sc/schedC2';
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();
    // const loan: any = JSON.parse(localStorage.getItem('LoanObj'));

    const hiddenFieldsObj: any = {
      api_call: '/sc/schedC2',
      line_number: 13,
      transaction_id: hiddenFields.transaction_id,
      back_ref_transaction_id: hiddenFields.back_ref_transaction_id,
      back_ref_sched_name: '',
      transaction_type: 'LOAN_FROM_IND',
      transaction_type_identifier: 'LOANS_OWED_BY_CMTE',
      entity_type: 'IND',
      entity_id: hiddenFields.entity_id,
      //also pass an additional attribute callled guarantor_entity_id since thats what is it is mapped to in db
      guarantor_entity_id: hiddenFields.entity_id
    };

    /*     const loanByCommFromIndObj: any = {
          api_call:'/sc/schedC',
          line_number: 13,
          //transaction_id:'16G',
          transaction_id:loan.transaction_id,
          back_ref_transaction_id: '',
          back_ref_sched_name: '',
          transaction_type: 'LOAN_FROM_IND',
          transaction_type_identifier:'LOANS_OWED_BY_CMTE'
        };
        const loanByCommFromBankObj: any = {
          api_call:'/sc/schedC',
          line_number: 13,
          //transaction_id:'16F',
          transaction_id:loan.transaction_id,
          back_ref_transaction_id: '',
          back_ref_sched_name: '',
          transaction_type: 'LOAN_FROM_BANK',
          transaction_type_identifier:'LOANS_OWED_BY_CMTE'
        };
        const loanToCommObj: any = {
          api_call:'/sc/schedC',
          line_number: 13,
          transaction_id:'',
          back_ref_transaction_id: '',
          back_ref_sched_name: '',
          transaction_type: 'LOAN_TO_COMM',
          transaction_type_identifier:'LOANS_OWED_TO_CMTE'
        }; */

    /*const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }*/

    //const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
    const formData: FormData = new FormData();
    let httpOptions = new HttpHeaders();
    let loanhiddenFields: any;
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);


    for (const [key, value] of Object.entries(endorserForm)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }

    /* if (transactionTypeIdentifier==='LOANS_OWED_BY_CMTE'){
      if (subType === 'IND'){
        loanhiddenFields= loanByCommFromIndObj;
      }else if (subType === 'ORG'){
        loanhiddenFields= loanByCommFromBankObj;  
      } 
    } else if (transactionTypeIdentifier==='LOANS_OWED_TO_CMTE'){
      loanhiddenFields= loanToCommObj;   
    } */
    loanhiddenFields = hiddenFieldsObj;

    //console.log("loanhiddenFields", loanhiddenFields);

    //Add loan hidden fields
    for (const [key, value] of Object.entries(loanhiddenFields)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }
    //console.log("saveSched_C reportId =", reportId);

    formData.append('report_id', reportId);

    if (scheduleAction === ScheduleActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              //console.log(" saveLoan called res...!", res);
              return res;
            }
            return false;
          })
        );
    } else if (scheduleAction === ScheduleActions.edit) {
      return this._http
        .put(`${environment.apiUrl}${url}`, formData, {
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
    } else {
    }
  }

  c1Exists(currentLoanData: any): any {
    if (currentLoanData && currentLoanData.child && Array.isArray(currentLoanData.child)) {
      let c1 = currentLoanData.child.filter(e => e.transaction_type_identifier === 'SC1');
      if (c1.length > 0) {
        return true;
      }
    }
    return false;
  }


}

