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
export class SchedH4Service {

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
    const url = '/sh4/schedH4';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    let params = new HttpParams();
    params = params.append('report_id', reportId);
    params = params.append('page', page.toString());
    params = params.append('itemsPerPage', itemsPerPage.toString());
    params = params.append('sortColumnName', sortColumnName);
    params = params.append('descending', `${descending}`);
    
    return this._http
      .get<{items: any[], totalItems: number}>(
        `${environment.apiUrl}${url}`,      
        {
          params,
          headers: httpOptions
        }
      )
      .pipe(map(res => {
        if (res) {
          return {
            //items: this.mapFromServerFields(res.items),
            items: res.items,
            totalItems: res.totalItems
          };
        } else {
          return {
            items: null,
            totalItems: 0
          };
        }
      })
      );
  }

  public saveH4Ratio(ratio: any): Observable<any> {
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
            //console.log('Save H4Ratio res: ', res);
            return res;
          }
          return false;
      })
      );
  }
    
}
