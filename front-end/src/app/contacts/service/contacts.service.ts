import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../environments/environment';
import { ContactModel } from '../model/contacts.model';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { FilterPipe, FilterTypeEnum } from 'src/app/shared/pipes/filter/filter.pipe';
import { ContactFilterModel } from '../model/contacts-filter.model';
import { DatePipe } from '@angular/common';
import { ZipCodePipe } from 'src/app/shared/pipes/zip-code/zip-code.pipe';
import { map } from 'rxjs/operators';

export interface GetContactsResponse {
  contacts: ContactModel[];
  totalAmount: number;
  totalcontactsCount: number;
  totalPages: number;

  // remove after API is renamed.
  itemsPerPage: number;
  'total pages': number;
}

export enum ContactActions {
  add = 'add',
  edit = 'edit'
}

@Injectable({
  providedIn: 'root'
})
export class ContactsService {

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
  public getContacts(
      formType: string,
      reportId: string,
      page: number,
      itemsPerPage: number,
      sortColumnName: string,
      descending: boolean,
      filters: ContactFilterModel): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/core/contacts';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // const serverSortColumnName = this.mapToSingleServerName(sortColumnName);

    const request: any = {};
    request.reportid = reportId;
    request.page = page;
    request.itemsPerPage = itemsPerPage;
    request.sortColumnName = sortColumnName;
    request.descending = descending;

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

    console.log(' Contact Table request = ', request);
    console.log(' Contact Table httpOptions = ', httpOptions);

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
            console.log('Contact Table res: ', res);

            return res;
          }
          return false;
      }));
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
  public getUserDeletedContacts(
    formType: string,
    reportId: string,
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean,
    filters: ContactFilterModel): Observable<any> {

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
    // const mockResponse: GetContactsResponse = {
    //   contacts: this.mockRestoreTrxArray,
    //   totalAmount: 0,
    //   totalContactCount: this.mockRestoreTrxArray.length,

    //   // remove after API is renamed.
    //   itemsPerPage: 5,
    //   'total pages': 0
    // };
    // return Observable.of(mockResponse);

    console.log(' Contact Recycle Bin Table request = ', request);
    console.log(' Contact Recycle Bin Table httpOptions = ', httpOptions);

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
      const model = new ContactModel({});
      model.type = row.type;
      model.id = row.id;
      model.name = row.name;
      model.street1 = row.street1;
      model.street2 = row.street_2;
      model.city = row.city;
      model.state = row.state;
      model.zip = row.zip;
      model.employer = row.employer;
      model.occupation = row.occupation;
      
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
      case 'type':
        name = 'type';
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
      default:
    }
    return name ? name : '';
  }


  /**
   * Map front-end model fields to server fields.
   *
   * TODO The API should be changed to pass the property names expected by the front end.
   */
  public mapToServerFields(model: ContactModel) {

    const serverObject: any = {};
    if (!model) {
      return serverObject;
    }

    serverObject.name =  model.name;
    serverObject.type = model.type;
    serverObject.id = model.id;
    serverObject.street1 = model.street1;
    serverObject.street2 = model.street2;
    serverObject.city = model.city;
    serverObject.state = model.state;
    serverObject.zip = model.zip;
    serverObject.employer = model.employer;
    serverObject.occupation = model.occupation;
    

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
      cnt.transaction_amount_ui = `$${cnt.transaction_amount}`;
      cnt.transaction_date_ui = this._datePipe.transform(cnt.transaction_date, 'MM/dd/yyyy');
      cnt.deleted_date_ui = this._datePipe.transform(cnt.deleted_date, 'MM/dd/yyyy');
      cnt.zip_code_ui = this._zipCodePipe.transform(cnt.zip_code);
    }
  }


  /**
   * This method handles filtering the contacts array and will be replaced
   * by a backend API.
   */
  public mockApplyFilters(response: any, filters: ContactFilterModel) {
    console.log("mockApplyFilters response =", response);
    console.log("mockApplyFilters filters =", filters);

    if (!response.contacts) {
      return;
    }

    if (!filters) {
      return;
    }

    let isFilter = false;

    /*if (filters.keywords) {
      if (response.contacts.length > 0 && filters.keywords.length > 0) {
        isFilter = true;

        const fields = [ 'type', 'id', 'name', 'employer', 'occupation'];

        for (let keyword of filters.keywords) {
          let filterType = FilterTypeEnum.contains;
          keyword = keyword.trim();
          if ((keyword.startsWith('"') && keyword.endsWith('"')) ||
              keyword.startsWith(`'`) && keyword.endsWith(`'`)) {
            filterType = FilterTypeEnum.exact;
            keyword = keyword.valueOf().substring(1, keyword.length - 1);
          }
          const filtered = this._filterPipe.transform(response.contacts, fields, keyword, filterType);
          response.contacts = filtered;
        }
      }
    }   */

    if (filters.filterStates) {
      console.log("filters.filterStates", filters.filterStates);
      if (filters.filterStates.length > 0) {
        isFilter = true;
        const fields = ['state'];
        let filteredStateArray = [];
        for (const state of filters.filterStates) {
          const filtered = this._filterPipe.transform(response.contacts, fields, state);
          filteredStateArray = filteredStateArray.concat(filtered);
        }
        response.contacts = filteredStateArray;
      }
    }

    if (filters.filterTypes) {
      console.log("filters.filterTypes", filters.filterTypes);
      if (filters.filterTypes.length > 0) {
        isFilter = true;
        const fields = ['type'];
        let filteredTypeArray = [];
        for (const type of filters.filterTypes) {
          const filtered = this._filterPipe.transform(response.contacts, fields, type);
          filteredTypeArray = filteredTypeArray.concat(filtered);
        }
        response.contacts = filteredTypeArray;
      }
    }

    console.log("response.contacts", response.contacts);
  }


  /**
   *
   * @param array
   * @param sortColumnName
   * @param descending
   */
  public sortContacts(array: any, sortColumnName: string, descending: boolean) {
    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(array, {property: sortColumnName, direction: direction});
    return array;
  }

  /**
   * Delete contacts from the Recyling Bin.
   *
   * @param contacts the contacts to delete
   */
  public deleteRecycleBinContact(contacts: Array<ContactModel>): Observable<any> {


    // mocking the server API until it is ready.

    for (const cnt of contacts) {
      const index = this.mockRestoreTrxArray.findIndex(
        item => item.transaction_id === cnt.id);

      if (index !== -1) {
        this.mockRestoreTrxArray.splice(index, 1);
      }
    }

    return Observable.of('');
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
   public trashOrRestoreContacts(action: string, reportId: string, contacts: Array<ContactModel>) {

    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/core/trash_restore_contacts';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    const actions = [];
    for (const cnt of contacts) {
      actions.push({
        action: action,
        transaction_id: cnt.id
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
    }));

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
   * @param      {ContactActions}  scheduleAction  The type of action to save (add, edit)
   */
  public saveSchedule(formType: string, scheduleAction: ContactActions): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/sa/schedA';
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
    const receipt: any = JSON.parse(localStorage.getItem(`form_${formType}_receipt`));
    const formData: FormData = new FormData();

    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    /**
     * This has to be removed.
     * I'm not hard coding anything any more.
     * Or this has to be changed to just lower case.  This is not a
     * good practice at all.  Please do better then this.
     */
    formData.append('cmte_id', committeeDetails.committeeid);
    // With Edit Report Functionality
    if (reportType.hasOwnProperty('reportId')) {
      formData.append('report_id', reportType.reportId);
    } else if (reportType.hasOwnProperty('reportid')) {
      formData.append('report_id', reportType.reportid);
    }

    console.log();

    for (const [key, value] of Object.entries(receipt)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }

    if (scheduleAction === ContactActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
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
    } else if (scheduleAction === ContactActions.edit) {
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
      console.log('unexpected ContactActions received - ' + scheduleAction);
    }
  }

  public getContactsDynamicFormFields(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/get_contacts_dynamic_forms_fields`;
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
   * Saves a schedule a using POST.  The POST API supports saving an existing
   * transaction.  Therefore, transaction_id is required in this API call.
   *
   * TODO consider modifying saveScheduleA() to support both POST and PUT.
   *
   * @param      {string}  formType  The form type
   */
  public putScheduleA(formType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/sa/schedA';
    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
    const receipt: any = JSON.parse(localStorage.getItem(`form_${formType}_receipt`));

    let httpOptions = new HttpHeaders();
    const formData: FormData = new FormData();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // Needed for update but not for add
    formData.append('transaction_id', receipt.transactionId);

    formData.append('cmte_id', committeeDetails.committeeid);
    // With Edit Report Functionality
    if (reportType.hasOwnProperty('reportId')) {
      formData.append('report_id', reportType.reportId);
    } else if (reportType.hasOwnProperty('reportid')) {
      formData.append('report_id', reportType.reportid);
    }

    // formData.append('report_id', reportType.reportId);
    formData.append('transaction_type', '15');
    formData.append('line_number', '11AI');
    formData.append('first_name', receipt.ContributorFirstName);
    formData.append('last_name', receipt.ContributorLastName);
    formData.append('state', receipt.ContributorState);
    formData.append('city', receipt.ContributorCity);
    formData.append('zip_code', receipt.ContributorZip);
    formData.append('occupation', receipt.ContributorOccupation);
    formData.append('employer', receipt.ContributorEmployer);
    formData.append('contribution_amount', receipt.ContributionAmount);
    formData.append('contribution_date', receipt.ContributionDate);
    // formData.append('contribution_aggregate', receipt.ContributionAggregate);
    formData.append('entity_type', receipt.EntityType);
    if (receipt.ContributorMiddleName !== null) {
      if (typeof receipt.ContributorMiddleName === 'string') {
        formData.append('middle_name', receipt.ContributorMiddleName);
      }
    }
    if (receipt.ContributorPrefix !== null) {
      if (typeof receipt.ContributorPrefix === 'string') {
        formData.append('prefix', receipt.ContributorPrefix);
      }
    }
    if (receipt.ContributorSuffix !== null) {
      if (typeof receipt.ContributorSuffix === 'string') {
        formData.append('suffix', receipt.ContributorSuffix);
      }
    }
    formData.append('street_1', receipt.ContributorStreet1);
    if (receipt.ContributorStreet2 !== null) {
      if (typeof receipt.ContributorStreet2 === 'string') {
        formData.append('street_2', receipt.ContributorStreet2);
      }
    }
    if (receipt.MemoText !== null) {
      if (typeof receipt.MemoText === 'string') {
        formData.append('memo_text', receipt.MemoText);
      }
    }
    if (receipt.MemoCode !== null) {
      if (typeof receipt.MemoCode === 'string') {
        formData.append('memo_code', receipt.MemoCode);
      }
    }
    if (receipt.ContributionPurposeDescription !== null) {
      if (typeof receipt.ContributionPurposeDescription === 'string') {
        formData.append('purpose_description', receipt.ContributionPurposeDescription);
      }
    }
    // if (receipt.ContributionAggregate !== null) {
    //   if (typeof receipt.ContributionAggregate === 'string') {
    //     formData.append('contribution_aggregate', receipt.ContributionAggregate);
    //   }
    // }

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
  }

}

