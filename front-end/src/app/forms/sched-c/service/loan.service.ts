import { Injectable } from '@angular/core';
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
  public getLoan(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sc/get_outstanding_loans';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    
    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            console.log('get_outstanding_loans API res: ', res);

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
    /* const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sc/get_outstanding_loans';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    
    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            console.log('get_outstanding_loans API res: ', res);

            return res;
          }
          return false;
      })); */

      return Observable.of(this.mockEndorserSummaryData);
  }

  /**
   * Get the contacts for the user's Recycling Bin by Report ID.
   * These are contacts "trashed" by the user.
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
  public getUserDeletedLoan(
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    ): Observable<any> {

    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/core/get_all_trashed_contacts';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    request.page = page;
    request.itemsPerPage = itemsPerPage;
    request.sortColumnName = sortColumnName;
    request.descending = descending;

    
    // For mock response - remove after API is verified
    // const mockResponse: GetLoanResponse = {
    //   contacts: this.mockRestoreTrxArray,
    //   totalAmount: 0,
    //   totalContactCount: this.mockRestoreTrxArray.length,

    //   // remove after API is renamed.
    //   itemsPerPage: 5,
    //   'total pages': 0
    // };
    // return Observable.of(mockResponse);

    return this._http
      .post(
        `${environment.apiUrl}${url}`,
        request,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            console.log('Contact Recycle Bin Table res: ', res);

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
      //model.selected = row.selected;
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
        name= 'loan_balance';
        break;
      case 'loan_incurred_date':
        name= 'loan_incurred_date';
        break;  
      case 'loan_due_date':
        name= 'loan_due_date';
        break;
      case 'loan_intrest_rate':
        name= 'loan_intrest_rate';
        break;
      case 'is_loan_secured':
        name= 'is_loan_secured';
        break;       
      case 'is_personal_funds':
        name= 'is_personal_funds';
        break;     
      case 'lender_cmte_id':
        name= 'lender_cmte_id';
        break;   
      case 'lender_cand_id':
        name= 'lender_cand_id';
        break;           
      case 'lender_cand_last_name':
        name= 'lender_cand_last_name';
        break;           
      case 'lender_cand_first_name':
        name= 'lender_cand_first_name';
        break;           
      case 'lender_cand_middle_name':
        name= 'lender_cand_middle_name';
        break;           
      case 'lender_cand_prefix':
        name= 'lender_cand_prefix';
        break;           
      case 'lender_cand_suffix':
        name= 'lender_cand_suffix';
        break;           
      case 'lender_cand_office':
        name= 'lender_cand_office';
        break;           
      case 'delete_ind':
        name= 'delete_ind';
        break;         
      case 'memo_text':
        name= 'memo_text';
        break;         
      case 'memo_code':
        name= 'memo_code';
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
    serverObject.name =  model.name;
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
    utc.setUTCHours(0,0,0,0);
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
    this._orderByPipe.transform(array, {property: sortColumnName, direction: direction});
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
    this._orderByPipe.transform(array, {property: sortColumnName, direction: direction});
    return array;
  }

  /**
   * Get transaction category types
   * 
   * @param formType
   */
  public getContactCategories(formType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
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
          console.log('Trash Restore response: ', res);
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

    console.log (" saveSched_C transactionTypeIdentifier =", transactionTypeIdentifier)
    console.log (" saveSched_C subType =", subType)

    for (const [key, value] of Object.entries(loan)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }
    
    if (transactionTypeIdentifier==='LOANS_OWED_BY_CMTE'){
      if (subType === 'IND'){
        loanhiddenFields= loanByCommFromIndObj;
      }else if (subType === 'ORG'){
        loanhiddenFields= loanByCommFromBankObj;  
      } 
    } else if (transactionTypeIdentifier==='LOANS_OWED_TO_CMTE'){
      loanhiddenFields= loanToCommObj;   
    }

    console.log ("loanhiddenFields", loanhiddenFields);

    //Add loan hidden fields
    for (const [key, value] of Object.entries(loanhiddenFields)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }
    console.log("saveSched_C reportId =", reportId);

    formData.append('report_id', reportId );

    if (scheduleAction === ScheduleActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              console.log(" saveLoan called res...!", res);
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
  public saveSched_C2(scheduleAction: ScheduleActions, endorserForm:any, hiddenFields: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/sc/schedC2';
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();
    // const loan: any = JSON.parse(localStorage.getItem('LoanObj'));
    
    const hiddenFieldsObj: any = {
      api_call:'/sc/schedC2',
      line_number: 13, 
      transaction_id:endorserForm.transaction_id,
      back_ref_transaction_id: hiddenFields.back_ref_transaction_id,
      back_ref_sched_name: '',
      transaction_type: 'LOAN_FROM_IND',
      transaction_type_identifier:'LOANS_OWED_BY_CMTE', 
      entity_id: hiddenFields.entity_id
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

    console.log ("loanhiddenFields", loanhiddenFields);

    //Add loan hidden fields
    for (const [key, value] of Object.entries(loanhiddenFields)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }
    console.log("saveSched_C reportId =", reportId);

    formData.append('report_id', reportId );

    if (scheduleAction === ScheduleActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              console.log(" saveLoan called res...!", res);
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


  /* private mockEndorserSummaryData =[{
    "first_name": "Candi",
    "last_name": "Redwin",
    "contribution_amount": 190,
    "employer": "Bubblemix",
    "occupation": "Marketing Manager"
  }, {
    "first_name": "Heddi",
    "last_name": "Swynley",
    "contribution_amount": 72,
    "employer": "Youbridge",
    "occupation": "Project Manager"
  }, {
    "first_name": "Malinde",
    "last_name": "Scanlon",
    "contribution_amount": 604,
    "employer": "Dynava",
    "occupation": "Executive Secretary"
  }, {
    "first_name": "Roberta",
    "last_name": "Browse",
    "contribution_amount": 172,
    "employer": "Skinder",
    "occupation": "Administrative Assistant III"
  }, {
    "first_name": "Clifford",
    "last_name": "Itskovitz",
    "contribution_amount": 661,
    "employer": "Thoughtblab",
    "occupation": "Senior Quality Engineer"
  }, {
    "first_name": "Moishe",
    "last_name": "Dechelette",
    "contribution_amount": 180,
    "employer": "Browseblab",
    "occupation": "Internal Auditor"
  }, {
    "first_name": "Kate",
    "last_name": "Salkeld",
    "contribution_amount": 752,
    "employer": "Tavu",
    "occupation": "Geologist III"
  }, {
    "first_name": "Darbee",
    "last_name": "Vail",
    "contribution_amount": 590,
    "employer": "Photospace",
    "occupation": "Chief Design Engineer"
  }, {
    "first_name": "Austine",
    "last_name": "Fransoni",
    "contribution_amount": 227,
    "employer": "Innotype",
    "occupation": "Systems Administrator I"
  }, {
    "first_name": "Lek",
    "last_name": "Dunbar",
    "contribution_amount": 813,
    "employer": "Edgeblab",
    "occupation": "Research Associate"
  }, {
    "first_name": "Joaquin",
    "last_name": "Cattrell",
    "contribution_amount": 477,
    "employer": "Linkbuzz",
    "occupation": "Financial Advisor"
  }, {
    "first_name": "Katherina",
    "last_name": "Seckom",
    "contribution_amount": 184,
    "employer": "Bubblemix",
    "occupation": "Media Manager I"
  }, {
    "first_name": "Cesar",
    "last_name": "Iohananof",
    "contribution_amount": 209,
    "employer": "Tagchat",
    "occupation": "Tax Accountant"
  }, {
    "first_name": "Gustaf",
    "last_name": "Tumayan",
    "contribution_amount": 55,
    "employer": "Brightbean",
    "occupation": "Systems Administrator III"
  }, {
    "first_name": "Moina",
    "last_name": "Vesty",
    "contribution_amount": 704,
    "employer": "Youfeed",
    "occupation": "Accounting Assistant IV"
  }, {
    "first_name": "Clarie",
    "last_name": "Rackley",
    "contribution_amount": 80,
    "employer": "Oyondu",
    "occupation": "VP Product Management"
  }, {
    "first_name": "Muhammad",
    "last_name": "Bezants",
    "contribution_amount": 559,
    "employer": "Camido",
    "occupation": "Analyst Programmer"
  }, {
    "first_name": "Clara",
    "last_name": "Heddy",
    "contribution_amount": 401,
    "employer": "Leexo",
    "occupation": "Product Engineer"
  }, {
    "first_name": "Blythe",
    "last_name": "Rouchy",
    "contribution_amount": 690,
    "employer": "Browsebug",
    "occupation": "Accountant I"
  }, {
    "first_name": "Graehme",
    "last_name": "Ahrend",
    "contribution_amount": 116,
    "employer": "Rhycero",
    "occupation": "Operator"
  }, {
    "first_name": "Torrence",
    "last_name": "Middler",
    "contribution_amount": 547,
    "employer": "Voomm",
    "occupation": "Human Resources Assistant II"
  }, {
    "first_name": "Tam",
    "last_name": "Blueman",
    "contribution_amount": 198,
    "employer": "Voonder",
    "occupation": "Research Associate"
  }, {
    "first_name": "Sheffie",
    "last_name": "Bibbie",
    "contribution_amount": 422,
    "employer": "Devpoint",
    "occupation": "Operator"
  }, {
    "first_name": "Amie",
    "last_name": "Sustin",
    "contribution_amount": 996,
    "employer": "Voonte",
    "occupation": "Physical Therapy Assistant"
  }, {
    "first_name": "Chery",
    "last_name": "Lindl",
    "contribution_amount": 77,
    "employer": "Brainsphere",
    "occupation": "Registered Nurse"
  }, {
    "first_name": "Arabella",
    "last_name": "Peatheyjohns",
    "contribution_amount": 791,
    "employer": "Zava",
    "occupation": "Compensation Analyst"
  }, {
    "first_name": "Leann",
    "last_name": "Aldis",
    "contribution_amount": 292,
    "employer": "Babblestorm",
    "occupation": "Food Chemist"
  }, {
    "first_name": "Lina",
    "last_name": "Gwyther",
    "contribution_amount": 518,
    "employer": "Skipfire",
    "occupation": "Chemical Engineer"
  }, {
    "first_name": "Mable",
    "last_name": "Sanchiz",
    "contribution_amount": 531,
    "employer": "Eazzy",
    "occupation": "Senior Developer"
  }, {
    "first_name": "Ezmeralda",
    "last_name": "Physick",
    "contribution_amount": 291,
    "employer": "Photobean",
    "occupation": "Physical Therapy Assistant"
  }, {
    "first_name": "Elnar",
    "last_name": "Catherick",
    "contribution_amount": 794,
    "employer": "Vinder",
    "occupation": "Structural Engineer"
  }, {
    "first_name": "Court",
    "last_name": "Scintsbury",
    "contribution_amount": 392,
    "employer": "Skajo",
    "occupation": "Speech Pathologist"
  }, {
    "first_name": "Jeni",
    "last_name": "Fortescue",
    "contribution_amount": 463,
    "employer": "Topicshots",
    "occupation": "Compensation Analyst"
  }, {
    "first_name": "Calvin",
    "last_name": "Kennefick",
    "contribution_amount": 95,
    "employer": "Thoughtstorm",
    "occupation": "Sales Representative"
  }, {
    "first_name": "Bink",
    "last_name": "Langran",
    "contribution_amount": 67,
    "employer": "Skivee",
    "occupation": "Help Desk Operator"
  }, {
    "first_name": "Andonis",
    "last_name": "Terrill",
    "contribution_amount": 210,
    "employer": "Twimm",
    "occupation": "Research Nurse"
  }, {
    "first_name": "Gilberta",
    "last_name": "Costerd",
    "contribution_amount": 966,
    "employer": "Kanoodle",
    "occupation": "Mechanical Systems Engineer"
  }, {
    "first_name": "Spense",
    "last_name": "Popham",
    "contribution_amount": 693,
    "employer": "Trudeo",
    "occupation": "Staff Accountant I"
  }, {
    "first_name": "Tandy",
    "last_name": "Twentyman",
    "contribution_amount": 172,
    "employer": "Dablist",
    "occupation": "Programmer Analyst III"
  }, {
    "first_name": "Taffy",
    "last_name": "Rowbottom",
    "contribution_amount": 348,
    "employer": "Thoughtbridge",
    "occupation": "VP Sales"
  }, {
    "first_name": "Maisey",
    "last_name": "Grinnell",
    "contribution_amount": 364,
    "employer": "Meevee",
    "occupation": "Financial Analyst"
  }, {
    "first_name": "Doris",
    "last_name": "Janks",
    "contribution_amount": 641,
    "employer": "Linklinks",
    "occupation": "Technical Writer"
  }, {
    "first_name": "Grady",
    "last_name": "Gemnett",
    "contribution_amount": 194,
    "employer": "Reallinks",
    "occupation": "Sales Representative"
  }, {
    "first_name": "Nathanael",
    "last_name": "Harron",
    "contribution_amount": 281,
    "employer": "Rhyzio",
    "occupation": "VP Accounting"
  }, {
    "first_name": "Kelci",
    "last_name": "Balle",
    "contribution_amount": 560,
    "employer": "Feedfire",
    "occupation": "Analyst Programmer"
  }, {
    "first_name": "Huntington",
    "last_name": "Littlemore",
    "contribution_amount": 359,
    "employer": "Flashdog",
    "occupation": "Technical Writer"
  }, {
    "first_name": "Frederique",
    "last_name": "Scriven",
    "contribution_amount": 170,
    "employer": "Edgeclub",
    "occupation": "Senior Quality Engineer"
  }, {
    "first_name": "Bartlet",
    "last_name": "Teresse",
    "contribution_amount": 878,
    "employer": "Kamba",
    "occupation": "Geologist IV"
  }, {
    "first_name": "Annabell",
    "last_name": "Beavan",
    "contribution_amount": 548,
    "employer": "Yodo",
    "occupation": "Chief Design Engineer"
  }, {
    "first_name": "Berky",
    "last_name": "Hixley",
    "contribution_amount": 456,
    "employer": "Realcube",
    "occupation": "Nurse"
  }] */
   private mockEndorserSummaryData = [{
    "first_name": "Kali",
    "last_name": "Reggio",
    "contribution_amount": 940,
    "employer": "Kwinu",
    "occupation": "Environmental Specialist"
  }, {
    "first_name": "Nathanil",
    "last_name": "Itzkin",
    "contribution_amount": 728,
    "employer": "Mudo",
    "occupation": "Environmental Tech"
  }, {
    "first_name": "Shurlocke",
    "last_name": "Gibbens",
    "contribution_amount": 666,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Myrna",
    "last_name": "Gofford",
    "contribution_amount": 459,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Curcio",
    "last_name": "Bamb",
    "contribution_amount": 871,
    "employer": "Jaxworks",
    "occupation": "Marketing Assistant"
  }, {
    "first_name": "Camille",
    "last_name": "Szimoni",
    "contribution_amount": 670,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Fraze",
    "last_name": "Chilcott",
    "contribution_amount": 280,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Edwina",
    "last_name": "Penney",
    "contribution_amount": 920,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Jennie",
    "last_name": "Petts",
    "contribution_amount": 310,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Jean",
    "last_name": "Maytom",
    "contribution_amount": 412,
    "employer": "Ozu",
    "occupation": "Computer Systems Analyst IV"
  }, {
    "first_name": "Dolorita",
    "last_name": "MacGlory",
    "contribution_amount": 822,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Kania",
    "last_name": "Chappelow",
    "contribution_amount": 460,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Kylen",
    "last_name": "Bryant",
    "contribution_amount": 694,
    "employer": "Avavee",
    "occupation": "Design Engineer"
  }, {
    "first_name": "Glen",
    "last_name": "Southam",
    "contribution_amount": 774,
    "employer": "Omba",
    "occupation": "Mechanical Systems Engineer"
  }, {
    "first_name": "Marina",
    "last_name": "Zavittieri",
    "contribution_amount": 826,
    "employer": "Skimia",
    "occupation": "Operator"
  }, {
    "first_name": "Marchall",
    "last_name": "Navan",
    "contribution_amount": 581,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Angel",
    "last_name": "Chatelain",
    "contribution_amount": 658,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Daniela",
    "last_name": "Abramino",
    "contribution_amount": 413,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Raynell",
    "last_name": "Ruppel",
    "contribution_amount": 371,
    "employer": "Rhyloo",
    "occupation": "Structural Engineer"
  }, {
    "first_name": "Rois",
    "last_name": "Josselson",
    "contribution_amount": 366,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Kinny",
    "last_name": "Skarman",
    "contribution_amount": 872,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Truman",
    "last_name": "Tuplin",
    "contribution_amount": 670,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Jeffry",
    "last_name": "Van Dalen",
    "contribution_amount": 995,
    "employer": "Dynava",
    "occupation": "Staff Accountant II"
  }, {
    "first_name": "Helene",
    "last_name": "Minker",
    "contribution_amount": 501,
    "employer": "Demizz",
    "occupation": "Physical Therapy Assistant"
  }, {
    "first_name": "Felice",
    "last_name": "Eggers",
    "contribution_amount": 566,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Shaine",
    "last_name": "Trundler",
    "contribution_amount": 965,
    "employer": "Devify",
    "occupation": "Information Systems Manager"
  }, {
    "first_name": "Em",
    "last_name": "De Avenell",
    "contribution_amount": 673,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Phip",
    "last_name": "Karlmann",
    "contribution_amount": 162,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Eudora",
    "last_name": "Salsbury",
    "contribution_amount": 908,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Latashia",
    "last_name": "Bathowe",
    "contribution_amount": 502,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Roberta",
    "last_name": "Garrold",
    "contribution_amount": 475,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Faythe",
    "last_name": "Haye",
    "contribution_amount": 850,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Liuka",
    "last_name": "Challener",
    "contribution_amount": 517,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Marcello",
    "last_name": "Timmermann",
    "contribution_amount": 596,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Tadio",
    "last_name": "Trowell",
    "contribution_amount": 479,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Emmery",
    "last_name": "Klossmann",
    "contribution_amount": 292,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Liana",
    "last_name": "Towler",
    "contribution_amount": 714,
    "employer": "Jabbertype",
    "occupation": "Engineer II"
  }, {
    "first_name": "Alano",
    "last_name": "Beaney",
    "contribution_amount": 835,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Holly-anne",
    "last_name": "Stowell",
    "contribution_amount": 707,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Ichabod",
    "last_name": "Guthrum",
    "contribution_amount": 407,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Ripley",
    "last_name": "Vinton",
    "contribution_amount": 833,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Josepha",
    "last_name": "Fawdrie",
    "contribution_amount": 763,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Carr",
    "last_name": "Featherbie",
    "contribution_amount": 666,
    "employer": "Camido",
    "occupation": "Assistant Professor"
  }, {
    "first_name": "Paulie",
    "last_name": "Sparhawk",
    "contribution_amount": 783,
    "employer": "Zoomcast",
    "occupation": "Food Chemist"
  }, {
    "first_name": "Ebeneser",
    "last_name": "Thoresbie",
    "contribution_amount": 647,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Alvy",
    "last_name": "Schoffel",
    "contribution_amount": 486,
    "employer": "Meevee",
    "occupation": "Help Desk Technician"
  }, {
    "first_name": "Beth",
    "last_name": "Crouch",
    "contribution_amount": 944,
    "employer": null,
    "occupation": null
  }, {
    "first_name": "Joelly",
    "last_name": "Whipple",
    "contribution_amount": 880,
    "employer": "Latz",
    "occupation": "Marketing Assistant"
  }, {
    "first_name": "Ron",
    "last_name": "Porcas",
    "contribution_amount": 818,
    "employer": "Babbleset",
    "occupation": "Information Systems Manager"
  }, {
    "first_name": "Myrna",
    "last_name": "Pollastro",
    "contribution_amount": 525,
    "employer": null,
    "occupation": null
  }]; 


}

