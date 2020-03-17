import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../environments/environment';
import { map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class SchedLService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) { }

  public getTransactions(reportId: string, levinType: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url = '/sl/get_sla_summary_table';
    if (levinType === 'LB_SUM') {
      url = '/sl/get_slb_summary_table';
    }

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
          if (res) {
            //console.log('SL Transactions res: ', res);
            return res;
          }
          return false;
      })
      );
  }

  public getSummary(reportId: string, levinAccountId: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sl/get_sl_summary_table';
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    let params = new HttpParams();
    params = params.append('report_id', reportId);
    params = params.append('levin_account_id', levinAccountId);
    params = params.append('calendar_year', new Date().getFullYear().toString());
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
            //console.log('SL Summary res: ', res);
            return res;
          }
          return false;
      })
      );
  }

  public cloneTransaction(transactionId: string) {

    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/core/clone_a_transaction';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
      .post(`${environment.apiUrl}${url}`, { transaction_id: transactionId }, {
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
  }

}
