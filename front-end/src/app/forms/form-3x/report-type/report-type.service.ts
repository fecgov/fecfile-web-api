import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, identity } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ReportTypeService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }

  /**
   * Gets the report types.
   *
   * @param      {string}  formType  The form type
   */
  public getReportTypes(formType: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url: string = '/core/get_report_types?form_type=F3X';
    let params = new HttpParams();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('form_type', `${formType}`);

    return this._http
       .get(
          `${environment.apiUrl}${url}`,
          {
            headers: httpOptions
          }
         );
   }

  /**
   * Saves a report.
   *
   * @param      {string}  formType  The form type
   */
  public saveReport(formType: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url: string = '/core/reports';


    let params = new HttpParams();
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const form3xReportType: any = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));

    formData.append('report_id', form3xReportType.reportId);
    formData.append('form_type', `F${formType}`);
    formData.append('amend_ind', form3xReportType.amend_Indicator);
    formData.append('report_type', form3xReportType.reportType);
    formData.append('election_code', form3xReportType.electionCode);
    if (form3xReportType.election_date.length >= 1) {
      formData.append('date_of_election', form3xReportType.election_date);
    }
    if (form3xReportType.election_state !== null) {
      if (typeof form3xReportType.election_state === 'string') {
        if (form3xReportType.election_state.length >= 1) {
          formData.append('state_of_election', form3xReportType.election_state);
        }
      }
    }
    formData.append('cvg_start_dt', form3xReportType.cvgStartDate);
    formData.append('cvg_end_dt', form3xReportType.cvgEndDate);
    formData.append('coh_bop', form3xReportType.coh_bop);

    return this._http
        .post(
          `${environment.apiUrl}${url}`,
          formData,
          {
            headers: httpOptions
          }
        )
        .pipe(map(res => {
            if (res) {
              if (localStorage.getItem(`form_${formType}_report_type`) !== null) {
                const reportObj: any = JSON.parse(window.localStorage.getItem(`form_${formType}_report_type`));

                reportObj.reportId = res[0].report_id;

                window.localStorage.setItem(`form_${formType}_report_type`, JSON.stringify(reportObj));
              }

              return res;
            }
            return false;
        }));
  }
}
