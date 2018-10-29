import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
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
    private _authService: AuthService,
    private _cookieService: CookieService
  ) { }

  /**
   * Logs a user into the API.
   *
   * @param      {String}  username  The username
   * @param      {String}  password  The password
   *
   * @return     {Observable}  The JSON web token response.
   */
  public signIn(username: string, password: string): Observable<any> {
    return this._http
      .post<Auth>(`${environment.apiUrl}/token/obtain`, {
        username,
        password
      })
      .pipe(map(res => {
          // login successful if there's a jwt token in the response
          if (res.token) {
             this._authService.doSignIn(res.token);
          }

          return res;
      }));
  }

  /**
   * Gets the commitee details.
   *
   * @return     {Observable}  The commitee details.
   */
  public getCommiteeDetails(): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));

    let httpOptions =  new HttpHeaders();
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
     .get(
        `${environment.apiUrl}/core/get_committee_details`,
        {
          headers: httpOptions
        }
      )
  }
}
