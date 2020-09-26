import { Injectable } from '@angular/core';
import {Observable} from 'rxjs';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {CookieService} from 'ngx-cookie-service';
import {environment} from '../../../../../environments/environment';
import {map} from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ManageUserService {
  

  constructor(  private _cookieService: CookieService,
                private _http: HttpClient) { }

  getUsers(): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/user/manage';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http.get(`${environment.apiUrl}${url}`, {
      headers: httpOptions
    });
  }

  toggleUser(id: number): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions = new HttpHeaders();
    const url = '/user/manage/toggle';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    const request: any = {};
    request.id = id;
    return this._http
        .put(`${environment.apiUrl}${url}`, request, {
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
  deleteUser(id: number): Observable<any> {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url = '/user/manage';

      const httpOptions = {
          headers: new HttpHeaders({
              'Content-Type': 'application/json',
              'Authorization': 'JWT ' + token,
          }),
          body: {
              id: id,
          },
      };
    return this._http
        .delete(`${environment.apiUrl}${url}`,  httpOptions)
        .pipe(
            map(res => {
              if (res) {
                return res;
              }
              return false;
            })
        );
  }

    saveUser(formData: any, isPost: boolean): Observable<any> {
        const token: string = JSON.parse(this._cookieService.get('user'));
        let httpOptions = new HttpHeaders();
        const url = '/user/manage';

        httpOptions = httpOptions.append('Content-Type', 'application/json');
        httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
        if (isPost) {
            return this._http
                .post(`${environment.apiUrl}${url}`, formData, {
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
        } else {
            return this._http
                .put(`${environment.apiUrl}${url}`, formData, {
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

    getTreasurerInfo(): Observable<any> {
        const token: string = JSON.parse(this._cookieService.get('user'));
        const url = `${environment.apiUrl}/core/get_committee_details`;
        let httpOptions = new HttpHeaders();

        httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
        httpOptions = httpOptions.append('Content-Type', 'application/json');
        return this._http.get(url, {
            headers: httpOptions,
        });
    }

    getSignedInUserInfo(): Observable<any> {
      const token: string = JSON.parse(this._cookieService.get('user'));
      const url = `${environment.apiUrl}/user/info`;
      let httpOptions = new HttpHeaders();

      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
      httpOptions = httpOptions.append('Content-Type', 'application/json');
      return this._http.get(url, {
          headers: httpOptions,
      });
  }

  authenticateUserWithRegToken(formData: any): Observable<any>{
    let httpOptions = new HttpHeaders();
    const url = '/user/register/authenticate';
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    return this._http
        .post(`${environment.apiUrl}${url}`, formData, {
            headers: httpOptions
        })
    }

    verifyCode(securityCode: string) : Observable<any>{
      let httpOptions = new HttpHeaders();
      const token: string = JSON.parse(this._cookieService.get('user'));
      const url = '/user/register/verify';
      let formData : any = {};
      formData.code = securityCode.toString();

      httpOptions = httpOptions.append('Content-Type', 'application/json');
      httpOptions = httpOptions.append('token', token);
      return this._http
          .post(`${environment.apiUrl}${url}`, formData, {
              headers: httpOptions
          })
    }

    createPassword(password:string): Observable<any>{
      let httpOptions = new HttpHeaders();
      const token: string = JSON.parse(this._cookieService.get('user'));
      const url = '/user/register/password';
      let formData : any = {};
      formData.password = password.toString();

      httpOptions = httpOptions.append('Content-Type', 'application/json');
      httpOptions = httpOptions.append('token', token);
      return this._http
          .post(`${environment.apiUrl}${url}`, formData, {
              headers: httpOptions
          })
    }
}
