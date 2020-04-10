import { Injectable } from '@angular/core';
import { CookieService } from 'ngx-cookie-service';
import { SessionService } from '../SessionService/session.service';
import * as jwt_decode from 'jwt-decode';
import {Roles} from '../../enums/Roles';
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
    this._session.destroy();
  }

  /**
   * Signs a user in if they have a access token.
   *
   * @param      {String}  accessToken  The access token
   */
  public doSignIn(accessToken: string) {
    if ((!accessToken)) {
      return;
    }
    this._session.accessToken = accessToken;

    this._cookieService.set('user', JSON.stringify(accessToken));
  }

  public getUserRole(): any {
    const sessionData = this._session.getSession();
    if (sessionData) {
      // TODO: return actual user role from JWT when implemented
      // for now C00415992 is Entry
      // for  now C00111476 is Readonly
      const decodedAccessToken = jwt_decode(sessionData);
      if ( decodedAccessToken.username === 'C00415992') {
        return Roles.Entry;
      } else if (decodedAccessToken.username === 'C00111476') {
        return Roles.ReadOnly;
      }
      return Roles.Admin;
    } else {
      return Roles.Admin;
    }
  }

  public isReadOnly(): boolean {
    const sessionData = this._session.getSession();
    if (sessionData) {
      // for now C00111476 is Readonly
      const decodedAccessToken = jwt_decode(sessionData);
      if (decodedAccessToken.username === 'C00111476') {
        return true;
      }
      return false;
    }
    }

    public isAdmin(): boolean {
      const sessionData = this._session.getSession();
      if (sessionData) {
        const decodedAccessToken = jwt_decode(sessionData);
        if (decodedAccessToken.username === 'C00111476' ||
            decodedAccessToken.username === 'C00415992' ) {
          return false;
        }
      }
      // All other committeeIds are Admin for now
      return true;
    }
}
