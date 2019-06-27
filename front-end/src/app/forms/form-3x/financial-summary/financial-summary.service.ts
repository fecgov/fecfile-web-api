import { identity } from 'rxjs';
import { map } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
import { UtilService } from '../../../shared/utils/util.service';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})

export class FinancialSummaryService {
  constructor(private _http: HttpClient, private _cookieService: CookieService, private _utilService: UtilService) {}
  /**
   * Gets the dynamic form fields.
   *
   * @param      {string}  formType         The form type
   * @param      {string}  transactionType  The transaction type
   */
  public getSummaryDetails(formType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/get_summary_table`;
    let reportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));
    let httpOptions = new HttpHeaders();
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    if (reportType === null || reportType === 'undefined' ){
      reportType = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
    }

    // With Edit Report Functionality
    if (reportType.hasOwnProperty('reportId')) {
      params = params.append('report_id', reportType.reportId);
    }
    else if (reportType.hasOwnProperty('reportid')) {
      params = params.append('report_id', reportType.reportid);
    }
    
    params = params.append('form_type', `F${formType}`);
    params = params.append('calendar_year', new Date().getFullYear().toString());
   
    return this._http.get(url, {
      headers: httpOptions,
      params
    });
  }
}