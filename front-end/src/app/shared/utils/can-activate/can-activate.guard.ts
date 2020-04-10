import { Injectable } from '@angular/core';
import { AuthService } from '../../services/AuthService/auth.service';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs';

@Injectable()
export class CanActivateGuard implements CanActivate {

  constructor(
    private auth: AuthService,
    private router: Router
  ) {}

  public canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | Promise<boolean> | boolean {

    const isSignedIn = this.auth.isSignedIn();
    let amIAllowed: boolean = false;
    if (isSignedIn) {
      const whoIsAllowed = route.data.role;
      const whoAmI = this.auth.getUserRole();

      if (whoIsAllowed) {
          for (const role of whoIsAllowed) {
            if (role === whoAmI) {
              amIAllowed = true;
            }
          }
          // TODO: check where to as per requirement?
          if (!amIAllowed) {
            // unauthorized
            this.router.navigate(['dashboard']);
          }
          return amIAllowed;
      } else {
        return true;
      }
    } else {
      this.router.navigate(['']);
      return false;
    }



  }

}
