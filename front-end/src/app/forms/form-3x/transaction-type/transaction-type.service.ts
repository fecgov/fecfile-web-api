import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { form3x_data, Icommittee_form3x_reporttype, form3XReport} from '../../../shared/interfaces/FormsService/FormsService';

@Injectable({
  providedIn: 'root'
})
export class TransactionTypeService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }

  /**
   * Gets the transaction categories.
   *
   * @param      {string}  formType  The form type
   */
  public getTransactionCategories( formType: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url: string = '';
    let params = new HttpParams();


    //url = '/f3x/get_transaction_categories?formType=F3X';
    url = '/core/get_transaction_categories?form_type=F3X';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', 'F3X');

    return this._http
       .get(
          `${environment.apiUrl}${url}`,
          {
           /* headers: httpOptions,
            params*/
            headers: httpOptions/*  */
          }
       );
  }
}
