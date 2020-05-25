import { TestBed, inject } from '@angular/core/testing';

import { TimeoutMessageService } from './timeout-message-service.service';

describe('TimeoutMessageServiceService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TimeoutMessageService]
    });
  });

  it('should be created', inject([TimeoutMessageService], (service: TimeoutMessageService) => {
    expect(service).toBeTruthy();
  }));
});
