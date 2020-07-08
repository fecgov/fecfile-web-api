import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../environments/environment';
import { map } from 'rxjs/operators';
import { Subscription } from 'rxjs';

export enum SchedHActions {
  add = 'add',
  edit = 'edit'
}

@Injectable({
  providedIn: 'root'
})
export class SchedH5Service {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) { }

  public getSummary(
      reportId: string,
      page: number,
      itemsPerPage: number,
      sortColumnName: string,
      descending: boolean
    ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sh5/get_h5_summary';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', reportId);
    params = params.append('page', page.toString());
    params = params.append('itemsPerPage', itemsPerPage.toString());
    params = params.append('sortColumnName', sortColumnName);
    params = params.append('descending', `${descending}`);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          params,
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          return res;
      }));
  }

  public getBreakDown(reportId: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sh5/get_sched_h5_breakdown';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', reportId);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          params,
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          return res;
        }));
  }




  public saveH5(h5: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sh5/schedH5';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const formData: FormData = new FormData();
    for (const [key, value] of Object.entries(h5)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }

    return this._http
      .post(
        `${environment.apiUrl}${url}`, h5,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
        if (res) {
          return res;
        }
        return false;
      })
      );
  }

  public getLevinAccounts(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/levin_accounts';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {         
          headers: httpOptions
        }
      )
      .pipe(map(res => {
        if (res) {
          return res;
        }
        return false;
      })
      );
  }

  public saveAndGetSummary(
      ratio: any, 
      reportId: string, 
      scheduleAction: SchedHActions,
      page: number,
      itemsPerPage: number,
      sortColumnName: string,
      descending: boolean
    ): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sh5/schedH5';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    const formData: FormData = new FormData();
    for (const [key, value] of Object.entries(ratio)) {
      if (value !== null) {
        if (typeof value === 'string') {
          formData.append(key, value);
        }
      }
    }

    if (scheduleAction === SchedHActions.add) {
      return this._http
        .post(
          `${environment.apiUrl}${url}`, ratio,
          {
            headers: httpOptions
          }
        );
      }
      else if(scheduleAction === SchedHActions.edit) {
        return this._http
        .put(
          `${environment.apiUrl}${url}`, ratio,
          {
            headers: httpOptions
          }
        );
      }

  }

  public getH1H2ExistStatus(report_id: string, activity_event_type: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sh1/validate_h1_h2_exist';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', report_id);
    params = params.append('activity_event_type', activity_event_type);
    params = params.append('calendar_year', new Date().getFullYear().toString());

    const committeeDetails: any = JSON.parse(localStorage.getItem('committee_details'));
    if (committeeDetails) {
      if (committeeDetails.cmte_type_category) {
        params = params.append('cmte_type_category', committeeDetails.cmte_type_category);
      }
    }

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          params,
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            //console.log('Validate H1 H2 exist res: ', res);
            return res;
          }
          return false;
      })
      );

  }

}
