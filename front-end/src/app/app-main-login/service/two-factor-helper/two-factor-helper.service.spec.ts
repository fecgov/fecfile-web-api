import { TestBed, inject } from '@angular/core/testing';

import { TwoFactorHelperService } from './two-factor-helper.service';

describe('TwoFactorHelperService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TwoFactorHelperService]
    });
  });

  it('should be created', inject([TwoFactorHelperService], (service: TwoFactorHelperService) => {
    expect(service).toBeTruthy();
  }));
});
