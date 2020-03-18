import { TestBed, inject } from '@angular/core/testing';

import { CsvConverterService } from './csv-converter.service';

describe('CsvConverterService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [CsvConverterService]
    });
  });

  it('should be created', inject([CsvConverterService], (service: CsvConverterService) => {
    expect(service).toBeTruthy();
  }));
});
