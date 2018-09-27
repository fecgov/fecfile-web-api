import { Injectable } from '@angular/core';
import { CookieService } from 'ngx-cookie-service';
import { SessionService } from '../SessionService/session.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(
    private _session: SessionService,
    private _cookieService: CookieService
  ) { }

  /**
   * Determines if signed in.
   *
   * @return     {boolean}  True if signed in, False otherwise.
   */
  public isSignedIn(): boolean {
    if (this._session.getSession()) {
      return true;
    }
    return false;
  }

  /**
   * Signs a user out of their session.
   *
   */
  public doSignOut() {
    console.log('doSignOut: ');
    this._session.destroy();
  }

  /**
   * Signs a user in if they have a access token.
   *
   * @param      {String}  accessToken  The access token
   */
  public doSignIn(accessToken: string) {
    console.log('doSignIn: ');
    if ((!accessToken)) {
      return;
    }
    this._session.accessToken = accessToken;

    this._cookieService.set('user', JSON.stringify(accessToken));
  }
}
