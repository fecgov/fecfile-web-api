import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CookieService } from 'ngx-cookie-service';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { AppConfigService } from '../../../app-config.service';
import { Auth } from '../../interfaces/APIService/APIService';
import { AuthService } from '../AuthService/auth.service';
import { SessionService } from '../SessionService/session.service';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(
    private _http: HttpClient,
    private _session: SessionService,
    private _authService: AuthService,
    private _cookieService: CookieService,
    private _appConfigService: AppConfigService
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
      .post<Auth>(`${this._appConfigService.getConfig().apiUrl}/token/obtain`, {
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
        `${this._appConfigService.getConfig().apiUrl}/core/get_committee_details`,
        {
          headers: httpOptions
        }
      )
  }

  /**
   * Gets the rad analyst.
   *
   * @return     {Observable}  The rad analyst.
   */
  public getRadAnalyst(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = '/f99/get_rad_analyst_info'; // This needs to be updated to /core/ on the server side.
    let httpOptions =  new HttpHeaders();
    let formData: FormData = new FormData();

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
      .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions
        }
      );
  }

  public getStates(): Observable<any>{
      const token: string = JSON.parse(this._cookieService.get('user'));
      const url: string = `${environment.apiUrl}/core/get_contacts_dynamic_forms_fields`;
      let httpOptions =  new HttpHeaders();
  
      httpOptions = httpOptions.append('Content-Type', 'application/json');
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
  
      return this._http
        .get(url,
          {
            headers: httpOptions
          }
        );
  }

  public getOfficesSought(): Observable<any>{
      const token: string = JSON.parse(this._cookieService.get('user'));
      const url: string = `${environment.apiUrl}/core/get_contacts_dynamic_forms_fields`;
      let httpOptions =  new HttpHeaders();
  
      httpOptions = httpOptions.append('Content-Type', 'application/json');
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
  
      return this._http
        .get(url,
          {
            headers: httpOptions
          }
        )
  }

}
