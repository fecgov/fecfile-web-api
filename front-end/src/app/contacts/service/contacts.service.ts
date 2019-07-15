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
  totalContactCount: number;
  totalPages: number;

  // remove after API is renamed.
  itemsPerPage: number;
  'total pages': number;
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
    const url = '/core/create_contacts_view';

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

    if (!response.contacts) {
      return;
    }

    if (!filters) {
      return;
    }

    let isFilter = false;

    if (filters.keywords) {
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
    }
   
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

  public getItemizations(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/core/get_ItemizationIndicators';
    let httpOptions =  new HttpHeaders();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
        .get(
          `${environment.apiUrl}${url}`,
          {
            headers: httpOptions
          }
        );
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
}
