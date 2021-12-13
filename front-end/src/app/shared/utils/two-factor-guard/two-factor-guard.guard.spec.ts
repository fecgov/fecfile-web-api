import { TestBed, inject, waitForAsync } from '@angular/core/testing';

import { TwoFactorGuardGuard } from './two-factor-guard.guard';

describe('TwoFactorGuardGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TwoFactorGuardGuard]
    });
  });

  it('should ...', inject([TwoFactorGuardGuard], (guard: TwoFactorGuardGuard) => {
    expect(guard).toBeTruthy();
  }));
});
