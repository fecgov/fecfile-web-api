import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { SessionService } from '../SessionService/session.service';
import { AuthService } from '../AuthService/auth.service';
import { Posts, Post, Auth } from '../../interfaces/APIService/APIService';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(
    private _http: HttpClient,
    private _session: SessionService,
    private _authService: AuthService
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
             this._authService.doSignIn(res.access_token);
          }

          return res;
      }));
  }
}
