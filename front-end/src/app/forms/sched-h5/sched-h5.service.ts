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
export class SchedH5Service {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
  ) { }

  public getSummary(reportId: string): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/sh5/get_h5_summary';

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
          console.log('H5 Summary Table res: ', res);
          return res;
        }
        return false;
      })
      );
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
        if (res) {
          console.log('H5 Breakdown res: ', res);
          return res;
        }
        return false;
      })
      );
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
          console.log('Save H5 res: ', res);
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
          console.log('Levin Accounts res: ', res);
          return res;
        }
        return false;
      })
      );
  }

  public saveAndGetSummary(ratio: any, reportId: string): Observable<any> {
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

    return this._http
      .post(
        `${environment.apiUrl}${url}`, ratio,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            console.log('Save H3Ratio res: ', res);

            //get summary
            //this.getSummary(reportId);

            let sub: Subscription;
            let sum: any;
            sub = this.getSummary(reportId).subscribe(res =>
              {
                if(res) {
                  sum =  res;
                }
              });

            return sum;
          }
          return false;
      })
      );


  }

}
