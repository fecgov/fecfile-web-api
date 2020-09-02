import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import {
  form3x_data,
  Icommittee_form3x_reporttype,
  form3XReport
} from '../../../shared/interfaces/FormsService/FormsService';

@Injectable({
  providedIn: 'root'
})
export class TransactionTypeService {
  constructor(private _http: HttpClient, private _cookieService: CookieService) {}

  /**
   * Gets the transaction categories.
   *
   * @param      {string}  formType  The form type
   */
  public getTransactionCategories(formType: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_transaction_categories';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', formType);

    let cmteTypeCategory = '';
    if (localStorage.getItem('committee_details') !== null) {
      const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
      if (committeeDetails.cmte_type_category !== null) {
        cmteTypeCategory = committeeDetails.cmte_type_category;
      }
    }
    params = params.append('cmte_type_category', cmteTypeCategory);

    return this._http.get(`${environment.apiUrl}${url}`, {
      params,
      headers: httpOptions
    });
  }

  /**
   * Get all transaction types 
   * @param formType 
   */
  public getTransactionTypes(formType: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    let url = '';
    let params = new HttpParams();

    url = '/core/get_transaction_types';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', 'F3X');

    return this._http.get(`${environment.apiUrl}${url}`, {
      params,
      headers: httpOptions
    });
  }
}
