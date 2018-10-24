import { TestBed, inject } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CookieService } from 'ngx-cookie-service';
import { FormsService } from './forms.service';

describe('FormsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule
      ],
      providers: [
        FormsService,
        CookieService
      ]
    });
  });

  it('should be created', inject([FormsService], (service: FormsService) => {
    expect(service).toBeTruthy();
  }));
});
