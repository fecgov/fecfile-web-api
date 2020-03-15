import { Subject } from 'rxjs/Subject';
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { map, switchMap, filter, take, tap } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../../environments/environment';
import * as jwt_decode from 'jwt-decode';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { AppConfigService } from '../../../app-config.service';
import { tokenKey } from '@angular/core/src/view';

@Injectable({
  providedIn: 'root'
})
export class SessionService {
  public accessToken: string;
  public readonly REFESH_TOKEN_THRESHOLD_IN_MINUTES = 15;
  private isRefreshing: any = false;
  private refreshTokenSubject :BehaviorSubject<any> = new BehaviorSubject<any>(null);

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService,
    private _appConfigService: AppConfigService
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

    localStorage.clear();
  }


  getToken(): string {
    let user = this._cookieService.get('user')
    if(user){
      return JSON.parse(user);
    }
    return null;
  }

  setToken(token: string): void {
    this._cookieService.set('user', JSON.stringify(token));
  }

  getTokenExpirationDate(token: string): Date {
    const decoded = jwt_decode(token);

    if (decoded.exp === undefined) return null;

    const date = new Date(0); 
    date.setUTCSeconds(decoded.exp);
    return date;
  }

  isSessionAboutToExpire(): boolean{
    let currentTime = new Date();
    currentTime.setMinutes(currentTime.getMinutes() + this.REFESH_TOKEN_THRESHOLD_IN_MINUTES);
    let minimumTimeToRefreshToken = new Date(currentTime.getTime());
    if(this.getToken()){
      const currentExpirationTime = this.getTokenExpirationDate(this.getToken());
      if(minimumTimeToRefreshToken > currentExpirationTime){
        return true;
      }
    }
    return false;
  }

  public refreshToken() {
    const currentToken = this.getToken();
    if(currentToken){
        
      if(!this.isRefreshing){
        this.isRefreshing = true;
        this.refreshTokenSubject.next(null);
        return this.getRefreshTokenFromServer(currentToken).pipe(
          tap((token:any)=>{
            this.setToken(token.token);
          }),
          switchMap((token:any) => {
            this.isRefreshing = false;
            this.refreshTokenSubject.next(token);
            return token;
          })
        );
      }
      else{
        return this.refreshTokenSubject.pipe(
          filter(token => token !== null),
          take(1),
          switchMap((token:any) =>{
            console.log('token ' + token);
            return token;
          })
        );
      }
    }
  }


  public getRefreshTokenFromServer(currentToken: string){
    if (this._appConfigService.getConfig() && this._appConfigService.getConfig().apiUrl) {
      return this._http
        .post(`${this._appConfigService.getConfig().apiUrl}/token/refresh`, {
          token: currentToken
        }).pipe(
          tap((tokens:any) =>{
            this.setToken(tokens.token);
          })
        );
    }
    return of({});
  }
}
