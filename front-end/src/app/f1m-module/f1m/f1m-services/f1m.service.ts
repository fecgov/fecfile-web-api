import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CookieService } from 'ngx-cookie-service';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { ScheduleActions } from 'src/app/forms/form-3x/individual-receipt/schedule-actions.enum';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class F1mService {


  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
    // private _reportTypeService: ReportTypeService,
    // private _activatedRoute: ActivatedRoute
    ) { }

    public saveForm(data:any,scheduleAction: ScheduleActions, stepType:string) : Observable<any>{
      const token: string = JSON.parse(this._cookieService.get('user'));
      let url: string = '/f1M/form1M';

      let httpOptions = new HttpHeaders();
      let params = new HttpParams();

      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
      params = params.append('step', stepType);
      
      if (scheduleAction === ScheduleActions.add) {
        return this._http
          .post(`${environment.apiUrl}${url}`, data, {
            params,
            headers: httpOptions,
          })
          .pipe(
            map(res => {
              if (res) {
                //console.log(" saveLoan called res...!", res);
                return res;
              }
              return false;
            })
          );
      } else if (scheduleAction === ScheduleActions.edit) {
        return this._http
          .put(`${environment.apiUrl}${url}`, data, {
            headers: httpOptions,
            params
          })
          .pipe(
            map(res => {
              if (res) {
                return res;
              }
              return false;
            })
          );
      } 
    }

}





