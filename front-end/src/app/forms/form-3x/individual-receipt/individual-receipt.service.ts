import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class IndividualReceiptService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }


 public getDynamicFormFields(formType: string, transactionType: string): Observable<any> {
  const token: string = JSON.parse(this._cookieService.get('user'));
  const url: string = '/core/get_dynamic_forms_fields';
  let httpOptions =  new HttpHeaders();
  let params = new HttpParams();
  let formData: FormData = new FormData();

  httpOptions = httpOptions.append('Content-Type', 'application/json');
  httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

  params = params.append('form_type', `F${formType}`);
  params = params.append('transaction_type', transactionType);

  return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions,
          params
        }
      );
 }
}
