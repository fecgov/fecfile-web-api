import { SessionService } from './../SessionService/session.service';
import { DialogService } from './../DialogService/dialog.service';
import { CookieService } from 'ngx-cookie-service';
import { AuthService } from './../AuthService/auth.service';
import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpResponse} from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { map, catchError, tap, switchMap, filter, take } from 'rxjs/operators';
import { Router } from '@angular/router';
import { ConfirmModalComponent } from '../../partials/confirm-modal/confirm-modal.component';
import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';

@Injectable({
  providedIn: 'root'
})
export class TokenInterceptorService implements HttpInterceptor{

  public readonly REFESH_TOKEN_THRESHOLD_IN_MINUTES = 30;
  private isRefreshing: any = false;
  private refreshTokenSubject :BehaviorSubject<any> = new BehaviorSubject<any>(null);

  constructor(private _cookieService: CookieService,
     private _router: Router, 
     private _dialogService: DialogService, 
     private _sessionService: SessionService, 
     ) { }



 intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
  let newHeaders = req.headers;
  const token = this._sessionService.getToken();
  if(token){
    this._sessionService.isSessionAboutToExpire();
  }

  if(this._sessionService.isSessionAboutToExpire()){
    this.refreshToken(req,next);
  }

   return next.handle(req).pipe(
    catchError(error => {
    this.showErrorMessageAndLogoutOn401(error);
    return throwError(error);
  })); 
}



  private showErrorMessageAndLogoutOn401(error: any) {
    if (error.status === 401) {
      this._sessionService.destroy();
      this._dialogService
        .confirm('The session has expired.', ConfirmModalComponent, 'Session Expired', false)
        .then(response => {
          if (response === 'okay' ||
            response === 'cancel' ||
            response === ModalDismissReasons.BACKDROP_CLICK ||
            response === ModalDismissReasons.ESC) {
            this._router.navigate(['']);
          }
        });
    }
  }

  public refreshToken(req: HttpRequest<any>, next: HttpHandler) {
    const currentToken = this._sessionService.getToken();
    if(currentToken){
      
      //check if token needs to be refreshed based on a time limit during this call
      if(!this.isRefreshing){
        this.isRefreshing = true;
        this.refreshTokenSubject.next(null);
        return this._sessionService.getRefreshTokenFromServer(currentToken).pipe(
          switchMap((token:any) => {
            this.isRefreshing = false;
            this.refreshTokenSubject.next(token);
            return next.handle(req);
          })
        ).subscribe(message => {this.isRefreshing = false;});
      }
      //else block any calls that may be invoked while token is being refreshed, until
      //token is refreshed, and then release those calls. 
      else{
        return this.refreshTokenSubject.pipe(
          filter(token => token !== null),
          take(1),
          switchMap(jwt =>{
            this.isRefreshing = false;
            return next.handle(req);
          }) 
        ).subscribe(message=> {
          this.isRefreshing = false;
        });
      }
    }
  }
}
