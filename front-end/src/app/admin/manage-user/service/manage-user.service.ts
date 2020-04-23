import { Injectable } from '@angular/core';
import {Observable} from 'rxjs';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {CookieService} from 'ngx-cookie-service';
import {environment} from '../../../../environments/environment';

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
}
