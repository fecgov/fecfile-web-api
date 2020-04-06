import { TestBed, inject } from '@angular/core/testing';

import { F1mService } from './f1m.service';

describe('F1mService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [F1mService]
    });
  });

  it('should be created', inject([F1mService], (service: F1mService) => {
    expect(service).toBeTruthy();
  }));
});
