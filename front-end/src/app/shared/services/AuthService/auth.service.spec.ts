import { TestBed, inject } from '@angular/core/testing';
import { CookieService } from 'ngx-cookie-service';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { SessionService } from '../SessionService/session.service';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let cookieService: CookieService;
  let authService: AuthService;
  let sessionService: SessionService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule
      ],
      providers: [
        AuthService,
        SessionService,
        CookieService
      ]
    });
  });

  beforeEach(() => {
    cookieService = TestBed.get(CookieService);

    authService = TestBed.get(AuthService);
    sessionService = TestBed.get(SessionService);
  });

  it('should be created', () => {
    expect(authService).toBeTruthy();
  });

  it('isSignedIn should indicate if your signed in', () => {
    cookieService.set('user', 'test');

    expect(authService.isSignedIn()).toBeTruthy();
  });

  it('isSignedIn should indicate if you are not signed in', () => {
    cookieService.delete('user');
    expect(authService.isSignedIn()).toBeFalsy();
  });

  it('doSignOut should sign you out', () => {
    cookieService.set('user', 'test');

    expect(authService.isSignedIn()).toBeTruthy();

    authService.doSignOut();

    expect(authService.isSignedIn()).toBeFalsy();
  });

  it('')
});
