import { HttpClient, HttpErrorResponse, HttpEvent, HttpHandler, HttpHeaders, HttpInterceptor, HttpRequest, HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { CookieService } from 'ngx-cookie-service';
import { Observable, of, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { AppConfigService } from '../../../app-config.service';
import { Auth } from '../../interfaces/APIService/APIService';
import { ConfirmModalComponent } from '../../partials/confirm-modal/confirm-modal.component';
import { AuthService } from '../AuthService/auth.service';
import { DialogService } from '../DialogService/dialog.service';
import { SessionService } from '../SessionService/session.service';

@Injectable({
  providedIn: 'root'
})
export class ApiService implements HttpInterceptor  {
  

  constructor(
    private _http: HttpClient,
    private _session: SessionService,
    private _authService: AuthService,
    private _cookieService: CookieService,
    private _appConfigService: AppConfigService,
    private _dialogService: DialogService
  ) { }

  private states: any[];

  /**
   * Logs a user into the API.
   *
   * @param      {String}  username  The username
   * @param      {String}  password  The password
   *
   * @return     {Observable}  The JSON web token response.
   */
  public signIn(email: string, cmteId: string, password: string): Observable<any> {

    // Django uses cmteId+email as unique username
    const username = cmteId + email;
    return this._http
      .post<Auth>(`${this._appConfigService.getConfig().apiUrl}/user/login/authenticate`, {
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
    const token: string = JSON.parse(this._cookieService.get('user'));

    let httpOptions =  new HttpHeaders();
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
     .get(
        `${this._appConfigService.getConfig().apiUrl}/core/get_committee_details`,
        {
          headers: httpOptions
        }
      );
  }

  getCommiteeDetailsForUnregisteredUsers() {
    const token: string = JSON.parse(this._cookieService.get('user'));

    let httpOptions =  new HttpHeaders();
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('token', token);

    return this._http
     .get(
        `${this._appConfigService.getConfig().apiUrl}/user/register/get_committee_details`,
        {
          headers: httpOptions
        }
      );
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

  public getCashOnHandInfoStatus(): Observable<any>{
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/core/cashOnHandInfoStatus`;
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

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (request.params.has("handleResponseError")) {
      return next.handle(request).pipe(
        catchError((error: HttpErrorResponse) => {
          let reason = error.statusText + '\n' +
            (error && error.error ? error.error : '');

          this._dialogService.checkIfModalOpen();
          this._dialogService
            .confirm(
              reason,
              ConfirmModalComponent,
              'Exception',
              false
            )
            .then(response => {
              if (response === 'okay') {
                this._dialogService.checkIfModalOpen();
              } else if (
                response === 'cancel' ||
                response !== ModalDismissReasons.BACKDROP_CLICK ||
                response !== ModalDismissReasons.ESC
              ) {
              }
            });

          return throwError(error);
        }));
    } else {
      return next.handle(request);
    }
  }
}
