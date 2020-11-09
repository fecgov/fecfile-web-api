import { TestBed, inject } from '@angular/core/testing';

import { ImportTransactionsService } from './import-transactions.service';

describe('ImportTransactionsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ImportTransactionsService]
    });
  });

  it('should be created', inject([ImportTransactionsService], (service: ImportTransactionsService) => {
    expect(service).toBeTruthy();
  }));
});
