import { TestBed, inject } from '@angular/core/testing';

import { FinancialSummaryService } from './financial-summary.service';

describe('FinancialSummaryService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FinancialSummaryService]
    });
  });

  it('should be created', inject([FinancialSummaryService], (service: FinancialSummaryService) => {
    expect(service).toBeTruthy();
  }));
});
