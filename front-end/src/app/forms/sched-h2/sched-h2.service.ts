import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../environments/environment';
import { map } from 'rxjs/operators';

export enum SchedHActions {
  add = 'add',
  edit = 'edit'
}

@Injectable({
  providedIn: 'root'
})
export class SchedH2Service {

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
    let httpOptions =  new HttpHeaders();
    const url = '/sh2/get_h2_summary_table';

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
          if (res) {
            //console.log('H2 Summary Table res: ', res);
            return res;
          }
          return false;
          })
      );
  }

  public saveH2Ratio(ratio: any, scheduleAction: SchedHActions): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    const url = '/sh2/schedH2';

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
        )
        .pipe(map(res => {
            if (res) {
              //console.log('Save H2Ratio res: ', res);
              return res;
            }
            return false;
        })
      );
    }else if(scheduleAction === SchedHActions.edit) {
      return this._http
        .put(
          `${environment.apiUrl}${url}`, ratio,
          {
            headers: httpOptions
          }
        )
        .pipe(map(res => {
            if (res) {
              //console.log('Edit H2Ratio res: ', res);
              return res;
            }
            return false;
        })
      );

    }
  }
    
}
