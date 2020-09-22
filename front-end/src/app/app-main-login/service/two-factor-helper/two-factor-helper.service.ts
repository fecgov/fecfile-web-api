import { Injectable } from '@angular/core';
import {CookieService} from 'ngx-cookie-service';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {environment} from '../../../../environments/environment';
import {map} from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class TwoFactorHelperService {


  constructor
  ( private _cookieService: CookieService,
                private _http: HttpClient ) { }

  requestCode(requestOption: string) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/password/reset/options';

    console.log('Option ' + requestOption);

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('token' , token);

    const option: any = { id : requestOption };

    return this._http
        .post(`${environment.apiUrl}${url}`, option, {
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

  validateCode(code: string) {
      const token: string = JSON.parse(this._cookieService.get('user'));
      let httpOptions = new HttpHeaders();
      const url = '/user/login/verify';

      httpOptions = httpOptions.append('Content-Type', 'application/json');
      httpOptions = httpOptions.append('token' , token);

      const option: any = { code : code };

      return this._http
          .post(`${environment.apiUrl}${url}`, option, {
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
