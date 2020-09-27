import { Injectable } from '@angular/core';
import {CookieService} from 'ngx-cookie-service';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {environment} from '../../../environments/environment';
import {map} from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class PasswordService {


  constructor
  (private _cookieService: CookieService,
   private _http: HttpClient) {
  }

  authenticate(committeeId: string, emailId: string) {
    const url = '/password/authenticate';

    const data: any = {committee_id: committeeId, email: emailId};

    return this._http
        .post(`${environment.apiUrl}${url}`, data)
        .pipe(
            map(res => {
              if (res) {
                return res;
              }
              return false;
            })
        );
  }

    verify(code: string) {
        const token: string = JSON.parse(this._cookieService.get('user'));
        let httpOptions = new HttpHeaders();
        const url = '/password/code/verify';


        httpOptions = httpOptions.append('Content-Type', 'application/json');
        httpOptions = httpOptions.append('token' , token);

        const body: any = { code: code};

        return this._http
            .post(`${environment.apiUrl}${url}`, body, {
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

    createPassword(newPassword: string) {
        const token: string = JSON.parse(this._cookieService.get('user'));
        let httpOptions = new HttpHeaders();
        const url = '/password/reset';

        httpOptions = httpOptions.append('Content-Type', 'application/json');
        httpOptions = httpOptions.append('token' , token);

        const body: any = { password: newPassword};

        return this._http
            .post(`${environment.apiUrl}${url}`, body, {
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
