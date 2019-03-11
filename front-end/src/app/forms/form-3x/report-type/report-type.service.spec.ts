import { TestBed, inject } from '@angular/core/testing';

import { ReportTypeService } from './report-type.service';

describe('ReportTypeService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ReportTypeService]
    });
  });

  it('should be created', inject([ReportTypeService], (service: ReportTypeService) => {
    expect(service).toBeTruthy();
  }));
});
