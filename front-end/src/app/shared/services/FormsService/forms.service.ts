import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { form99 } from '../../interfaces/FormsService/FormsService';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FormsService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }

  /**
   * Gets the form.
   *
   * @param      {String}   committee_id  The committee identifier.
   * @param      {boolean}  is_submitted  Indicates if submitted.
   * @param      {String}   form_type     The form type.
   *
   * @return     {Observable} The form being retreived.
   */
  public getForm(committee_id: string, is_submitted: boolean, form_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let params = new HttpParams();
    let url: string = '';

    if(form_type === '99') {
      url = '/f99/fetch_f99_info';
    }

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('committeeid', committee_id);
    params = params.append('is_submitted', is_submitted.toString());

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
   * Validates a form
   *
   * @param      {Object}  formObj    The form object.
   * @param      {String}  form_type  The form type.
   *
   * @return     {Observable}  The validation results of the form.
   */
  public validateForm(formObj: any, form_type: string): Observable<any> {
    console.log('validateForm: ');
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url: string = '';
    let data: any = {};

    if(form_type === '99') {
      let form99_details: form99 = JSON.parse(localStorage.getItem('form_99_details'));

      url = '/f99/validate_f99';

      data = form99_details;

      data.text = data.text.replace(/<[^>]*>/g, '');

      data.text = data.text.replace(/(&nbsp;)/g, ' ');

      console.log('data.text: ', data.text);
    }

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
      .post<form99>(
        `${environment.apiUrl}${url}`,
        data,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            return true;
          }
          return false;
      }));

  }

  /**
   * Saves a form.
   *
   * @param      {Object}  formObj    The form object.
   * @param      {String}  form_type  The form type.
   *
   * @return     {Observable} The result of the form being saved.
   */
  public saveForm(formObj: any, form_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let data: any = {};
    let httpOptions =  new HttpHeaders();
    let url: string = '';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    if(form_type === '99') {
      let form99_details: form99 = JSON.parse(localStorage.getItem('form_99_details'));

      console.log('form99_details: ', form99_details);

      url = '/f99/create_f99_info';
      data = form99_details;
    }

    return this._http
      .post(
        `${environment.apiUrl}${url}`,
        data,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            return true;
          }
          return false;
      }));

  }

  /**
   * Submits a form.
   *
   * @param      {Object}  formObj    The form object.
   * @param      {String}  form_type  The form type.
   *
   * @return     {Observable}  The result of submitting a form.
   */
  public submitForm(formObj: any, form_type): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let data: any = {};
    let httpOptions =  new HttpHeaders();
    let url: string = '';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    if(form_type === '99') {
      let form99_details: form99 = JSON.parse(localStorage.getItem('form_99_details'));

      url = '/f99/submit_comm_info';
      data = form99_details;
    }

    return this._http
      .post(
        `${environment.apiUrl}${url}`,
        data,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            return true;
          }
          return false;
      }));
  }
}
