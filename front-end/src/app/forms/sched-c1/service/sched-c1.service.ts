import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { ScheduleActions } from '../../form-3x/individual-receipt/schedule-actions.enum';
import { ReportTypeService } from '../../form-3x/report-type/report-type.service';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class SchedC1Service {
  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
    private _reportTypeService: ReportTypeService
  ) {}

  /**
   * Saves a C1 schedule.
   *
   * @param      {string}           formType  The form type
   * @param      {ScheduleActions}  scheduleAction  The type of action to save (add, edit)
   * @param      {any}              data The data to add to the POST/PUT request
   */
  public saveScheduleC1(formType: string, scheduleAction: ScheduleActions, data: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/sc/schedC1';
    const reportId: string = this._reportTypeService.getReportIdFromStorage('3X').toString();

    const formData: FormData = new FormData();
    const httpOptions = new HttpHeaders().append('Authorization', 'JWT ' + token);
    formData.append('report_id', reportId);
    formData.append('transaction_type_identifier', 'SC1');
    formData.append('entity_type', 'ORG'); 

    for (const [key, value] of Object.entries(data)) {
      if (value) {
        if (typeof value === 'string') {
          formData.append(key, value);
        } else if (value.hasOwnProperty('filename')) {
          // TODO add the BLOB
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
              //console.log(' saveLoan called res...!', res);
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
}
