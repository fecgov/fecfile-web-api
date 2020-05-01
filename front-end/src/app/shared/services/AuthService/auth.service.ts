import {Injectable} from '@angular/core';
import {CookieService} from 'ngx-cookie-service';
import {SessionService} from '../SessionService/session.service';
import * as jwt_decode from 'jwt-decode';
import {Roles} from '../../enums/Roles';

@Injectable({
    providedIn: 'root'
})
export class AuthService {

    constructor(
        private _session: SessionService,
        private _cookieService: CookieService
    ) {
    }

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
            const decodedAccessToken = jwt_decode(sessionData);
            return decodedAccessToken.role;
        }
        this.destroySession();
    }

    public isReadOnly(): boolean {
        const sessionData = this._session.getSession();
        if (sessionData) {
            const decodedAccessToken = jwt_decode(sessionData);
            if (decodedAccessToken.role === Roles.Upload || decodedAccessToken.role === Roles.ReadOnly) {
                return true;
            }
            return false;
        }
        this.destroySession();
    }

    public isUploader(): boolean {
        const sessionData = this._session.getSession();
        if (sessionData) {
            const decodedAccessToken = jwt_decode(sessionData);
            if (decodedAccessToken.role === Roles.Upload) {
                return true;
            }
            return false;
        }
        this.destroySession();
    }

    public isCommitteeAdmin(): boolean {
        const sessionData = this._session.getSession();
        if (sessionData) {
            const decodedAccessToken = jwt_decode(sessionData);
            if (decodedAccessToken.role === Roles.CommitteeAdmin) {
                return true;
            } else {
                return false;
            }
        }
        this.destroySession();
    }

    public isAdmin(): boolean {
        const sessionData = this._session.getSession();
        if (sessionData) {
            const decodedAccessToken = jwt_decode(sessionData);
            if (decodedAccessToken.role === Roles.Admin) {
                return true;
            } else {
                return false;
            }
        }
        this.destroySession();
    }

    private destroySession() {
        console.error('Session not found !!!');
        this._session.destroy();
    }
}
