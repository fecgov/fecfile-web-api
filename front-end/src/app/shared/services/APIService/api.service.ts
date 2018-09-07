import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import { SessionService } from '../SessionService/session.service';
import { Posts, Post, Auth } from '../../interfaces/APIService/APIService';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
    private _session: SessionService
  ) { }

  /**
   * Logs a user into the API.
   *
   * @param      {String}  username  The username
   * @param      {String}  password  The password
   * @return     {Object}  The JSON web token response.
   */
  public signIn(username: string, password: string) {
    return this._http
      .post<Auth>(`${environment.apiUrl}/auth/login`, {
        username,
        password
      })
      .pipe(map(res => {
          // login successful if there's a jwt token in the response
          if (res && res.access_token) {
              this._cookieService.set('user', JSON.stringify(res));
          }

          return res;
      }));
  }
}
