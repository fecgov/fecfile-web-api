// import { SessionService } from './../SessionService/session.service';
// import { DialogService } from './../DialogService/dialog.service';
// import { CookieService } from 'ngx-cookie-service';
// import { AuthService } from './../AuthService/auth.service';
// import { Injectable } from '@angular/core';
// import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpResponse} from '@angular/common/http';
// import { Observable, throwError } from 'rxjs';
// import { map, catchError } from 'rxjs/operators';
// import { Router } from '@angular/router';
// import { ConfirmModalComponent } from '../../partials/confirm-modal/confirm-modal.component';
// import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';

// @Injectable({
//   providedIn: 'root'
// })
// export class TokenInterceptorService implements HttpInterceptor{

//   constructor(private _cookieService: CookieService,
//      private _router: Router, 
//      private _dialogService: DialogService, 
//      private _sessionService: SessionService
//      ) { }

//   intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
//     console.log('REQUEST INTERCEPTOR');
//     let newHeaders = req.headers;
//     // uncomment next block of code once set up
//     /* 
//     const user = this._cookieService.get('user');
//     if(user){
//       const token: string = JSON.parse(user);
//       if (token) {
//          newHeaders = newHeaders.append('Authorization', token);
//       }

//     } */
//     //clone is required because HttpRequest is immutable object
//     const authReq = req.clone({headers: newHeaders});
//     return next.handle(authReq).pipe(map(resp => {
//       if(resp instanceof HttpResponse){
//         // this._authService.currentFakeValueToken = new Date();
        
//         return  resp;
//       }
//     }),catchError(error => {
//       if(error.status === 401){
//         this._sessionService.destroy();
//         this._dialogService
//             .confirm('The session has expired.', ConfirmModalComponent, 'Session Expired', false)
//             .then(response => {
//               if (
//                 response === 'okay' ||
//                 response === 'cancel' ||
//                 response === ModalDismissReasons.BACKDROP_CLICK ||
//                 response === ModalDismissReasons.ESC
//               ) {
//                 this._router.navigate(['']);
//               }
//             });
//       }
//       return throwError(error);
//     }));
//  }
// }
