import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../environments/environment';
import { map } from 'rxjs/operators';
import { Subscription } from 'rxjs';


@Injectable({
  providedIn: 'root'
})
export class SchedHServiceService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) { }

  public getSchedule(transaction:any): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = transaction.apiCall;

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', transaction.reportId);
    params = params.append('transaction_id', transaction.transactionId);
    
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
            return res;
          }
          return false;
      })
      );
  }

    
}
