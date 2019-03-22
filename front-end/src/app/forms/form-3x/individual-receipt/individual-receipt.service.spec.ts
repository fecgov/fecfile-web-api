import { TestBed, inject } from '@angular/core/testing';

import { IndividualReceiptService } from './individual-receipt.service';

describe('IndividualReceiptService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [IndividualReceiptService]
    });
  });

  it('should be created', inject([IndividualReceiptService], (service: IndividualReceiptService) => {
    expect(service).toBeTruthy();
  }));
});
