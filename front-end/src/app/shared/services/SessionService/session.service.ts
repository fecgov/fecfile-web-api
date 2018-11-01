import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SessionService {
  public accessToken: string;

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }

  /**
   * Returns the session token if it exists in local storage.
   *
   * @return     {Object}  The session.
   */
  public getSession() {
    if (this._cookieService.get('user')) {
      return this._cookieService.get('user');
    }
    return 0;
  }

  /**
   * Removes the active session and logs a user out.
   *
   */
  public destroy(): void {
    this.accessToken = null;
    this._cookieService.deleteAll();

<<<<<<< HEAD
    // this._cookieService.delete('user');

    this._cookieService.deleteAll();
=======
    localStorage.clear();
>>>>>>> develop
  }
}
