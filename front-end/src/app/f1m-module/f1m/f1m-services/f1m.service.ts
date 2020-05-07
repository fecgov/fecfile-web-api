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
    ) { }

    public getForm(reportId: string): Observable<any> {
      let token: string = JSON.parse(this._cookieService.get('user'));
      let httpOptions = new HttpHeaders();
      let params = new HttpParams();
      let url: string = '/f1M/form1M'
      
      params = params.append('reportId', reportId);
  
      httpOptions = httpOptions.append('Content-Type', 'application/json');
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
  
      return this._http
        .get(`${environment.apiUrl}${url}`, {
          headers: httpOptions,
          params
        })
    }

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


    public getDates(dateType:string, reportId:string = null, fifty_first_contributor_date: string = null) : Observable<any>{
      const token: string = JSON.parse(this._cookieService.get('user'));
      let url: string = '/f1M/' + dateType;
      let httpOptions = new HttpHeaders();
      let data :any = {};
      if(dateType === 'get_cmte_met_req_date' && reportId && fifty_first_contributor_date){
        data.reportId = reportId;
        data.fifty_first_contributor_date = fifty_first_contributor_date;
      }

      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
      
        return this._http
          .post(`${environment.apiUrl}${url}`,data ,{
            headers: httpOptions,
          })
    }

    public trashCandidate(candidate: any, reportId: string) :  Observable<any>{
      const token: string = JSON.parse(this._cookieService.get('user'));
      const url: string = `${environment.apiUrl}/f1M/delete_cand_f1m`;
  
      let httpOptions = new HttpHeaders();
  
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
      httpOptions = httpOptions.append('Content-Type', 'application/json');
  
      let params = new HttpParams();
      params = params.append('reportId', reportId);
      params = params.append('candidate_number', candidate.candidate_number);
  
      return this._http.delete(url, {
        params,
        headers: httpOptions
      });
    }
}





