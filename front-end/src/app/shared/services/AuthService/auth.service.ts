import { Injectable } from '@angular/core';
import { SessionService } from '../SessionService/session.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(
    private _session: SessionService
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
  }
}
