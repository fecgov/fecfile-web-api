import { Injectable } from '@angular/core';
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
            console.log('SL Transactions res: ', res);
            return res;
          }
          return false;
      })
      );
  }

  /*public saveH4Ratio(ratio: any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sh4/schedH4';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
      .post(
        `${environment.apiUrl}${url}`, ratio,    
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            console.log('Save H4Ratio res: ', res);
            return res;
          }
          return false;
      })
      );
  }*/
    
}
