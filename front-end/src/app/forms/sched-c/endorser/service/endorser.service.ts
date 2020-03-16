import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../../environments/environment';
import { EndorserModel } from '../model/endorser.model';
import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { FilterPipe, FilterTypeEnum } from 'src/app/shared/pipes/filter/filter.pipe';
//import { ContactFilterModel } from '../model/contacts-filter.model';
import { DatePipe } from '@angular/common';
import { ZipCodePipe } from 'src/app/shared/pipes/zip-code/zip-code.pipe';
import { map } from 'rxjs/operators';
import { ScheduleActions } from '../../../form-3x/individual-receipt/schedule-actions.enum';

export interface GetEndorsersResponse {
  contacts: EndorserModel[];
  totalAmount: number;
  totalcontactsCount: number;
  totalPages: number;

  // remove after API is renamed.
  itemsPerPage: number;
  'total pages': number;
}

export enum EndorsersActions {
  add = 'add',
  edit = 'edit'
}

@Injectable({
  providedIn: 'root'
})
export class EndorserService {

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
      descending: boolean): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/core/contactsTable';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    // const serverSortColumnName = this.mapToSingleServerName(sortColumnName);

    const request: any = {};
    request.reportid = reportId;
    request.page = page;
    request.itemsPerPage = itemsPerPage;
    request.sortColumnName = sortColumnName;
    request.descending = descending;

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
            //console.log('Contact Table res: ', res);

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
    page: number,
    itemsPerPage: number,
    sortColumnName: string,
    descending: boolean): Observable<any> {

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
            //console.log('Contact Recycle Bin Table res: ', res);

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
      const model = new EndorserModel({});
      model.entity_type = row.entity_type;
      model.id = row.id;
      model.name = row.name;
      model.street1 = row.street1;
      model.street2 = row.street2;
      model.city = row.city;
      model.state = row.state;
      model.zip = row.zip;
      model.employer = row.employer;
      model.occupation = row.occupation;
      model.entity_name = row.entity_name;
      model.contribution_amount = row.contribution_amount;
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
      case 'entityName':
        name= 'entityName';
        break;
      case 'officeSought':
        name= 'officeSought';
        break;  
      case 'candOffice':
        name= 'candOffice';
        break;
      case 'candOfficeState':
        name= 'candOfficeState';
        break;
      case 'candOfficeDistrict':
        name= 'candOfficeDistrict';
        break;       
      case 'candCmteId':
        name= 'candCmteId';
        break;     
      case 'deletedDate':
        name= 'deletedDate';
        break;   
      case 'activeTransactionsCnt':
        name= 'activeTransactionsCnt';
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
  public mapToServerFields(model: EndorserModel) {

    const serverObject: any = {};
    if (!model) {
      return serverObject;
    }

    serverObject.name =  model.name;
    serverObject.entity_type = model.entity_type;
    serverObject.id = model.id;
    serverObject.street1 = model.street1;
    serverObject.street2 = model.street2;
    serverObject.city = model.city;
    serverObject.state = model.state;
    serverObject.zip = model.zip;
    serverObject.employer = model.employer;
    serverObject.occupation = model.occupation;
    serverObject.contribution_amount = model.contribution_amount;
    serverObject.entityName = model.entity_name;
    
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
  public sortContacts(array: any, sortColumnName: string, descending: boolean) {
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
   public trashOrRestoreContacts(action: string, contacts: Array<EndorserModel>) {

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
   * @param      {EndorsersActions}  scheduleAction  The type of action to save (add, edit)
   */
  public saveContact(scheduleAction: ScheduleActions): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/core/contacts';
    /*const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }*/

    //const transactionType: any = JSON.parse(localStorage.getItem(`form_${formType}_transaction_type`));
    const contact: any = JSON.parse(localStorage.getItem(`contactObj`));
    const formData: FormData = new FormData();
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    for (const [key, value] of Object.entries(contact)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);

        }
      }
    }

    if (scheduleAction === ScheduleActions.add) {
      return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
          headers: httpOptions
        })
        .pipe(
          map(res => {
            if (res) {
              //console.log(" saveContact called res...!", res);
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

  public get_sched_c_endorser_dynamic_forms_fields(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/get_dynamic_forms_fields?form_type=F3X&transaction_type=SC2`;
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(url, {
      headers: httpOptions
    });
  }
  
  
  public deleteRecycleBinContact(contacts: Array<EndorserModel>): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/delete_trashed_contacts';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const request: any = {};
    const actions = [];
    for (const con of contacts) {
      actions.push({
        id: con.id
      });
    }
    request.actions = actions;

    return this._http
      .post(`${environment.apiUrl}${url}`, request, {
        headers: httpOptions
      })
     .map(res => {
          return false;
        });
  }

}

