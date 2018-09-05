import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRouteSnapshot, CanActivate, Router, Routes, RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { routes, AppRoutingModule } from './app-routing.module';
import { CanActivateGuard } from '../shared/utils/can-activate/can-activate.guard';
import { AuthService } from '../shared/services/AuthService/auth.service';
import { AppComponent } from '../app.component';
import { LoginComponent } from '../login/login.component';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { ProfileComponent } from '../profile/profile.component';

class MockAuthService extends AuthService {
  public isSignedIn(): boolean {
    return true;
  }
}

class MockCanActivateGuard extends CanActivateGuard {
  public canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | Promise<boolean> | boolean {
    return true;
  }
}

describe('AppRoutingModule', () => {
  let appRoutingModule: AppRoutingModule;
  let canActivateGuard: MockCanActivateGuard;
  let location: Location;
  let router: Router;
  let fixture;

  beforeEach(() => {
    appRoutingModule = new AppRoutingModule();

    TestBed.configureTestingModule({
      schemas: [ NO_ERRORS_SCHEMA ],
      imports: [
        FormsModule,
        ReactiveFormsModule,
        RouterTestingModule.withRoutes(routes)
      ],
      declarations: [
        AppComponent,
        LoginComponent,
        DashboardComponent,
        ProfileComponent
      ],
      providers: [
        FormBuilder,
        {
          provide: CanActivateGuard,
          useClass: MockCanActivateGuard
        }
      ]
    });

    router = TestBed.get(Router);
    location = TestBed.get(Location);

    fixture = TestBed.createComponent(AppComponent);
    router.initialNavigation();
  });

  it('should create an instance', () => {
    expect(appRoutingModule).toBeTruthy();
  });

  it('navigate to "" redirects you to login', fakeAsync(() => {
    router.navigate(['']);
    tick();
    expect(location.path()).toBe('');
  }));

  it('cannot navigate to "/dashboard" if not logged in', fakeAsync(() => {
    router.navigate(['/dashboard']);
    tick();
    expect(location.path()).toBeFalsy('/dashboard');
  }));

  it('cannot navigate to "/profile" if not logged in', fakeAsync(() => {
    router.navigate(['/profile']);
    tick();
    expect(location.path()).toBeFalsy('/profile');
  }));

  it('should navigate to "/dashboard" if logged in', fakeAsync(() => {
    router.navigate(['/dashboard']);
    tick();
    expect(location.path()).toBe('/dashboard');
  }));
});
