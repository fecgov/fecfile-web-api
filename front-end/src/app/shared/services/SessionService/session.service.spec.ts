import { TestBed, inject } from '@angular/core/testing';
import { CookieService } from 'ngx-cookie-service';
import { SessionService } from './session.service';

describe('SessionService', () => {

  let cookieService: CookieService;
  let sessionService: SessionService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        SessionService,
        CookieService
      ]
    });
  });

  beforeEach(() => {
    cookieService = TestBed.get(CookieService);

    sessionService = TestBed.get(SessionService);
  });

  it('should be created', () => {
    expect(sessionService).toBeTruthy();
  });

  it('should get session cookie', () => {
    cookieService.set('user', 'test');

    expect(sessionService.getSession()).toBe('test');
  });

  it('should destroy session cookie', () => {
    cookieService.delete('user');

    expect(sessionService.getSession()).toBe(0);
  });
});
