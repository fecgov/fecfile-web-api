import { TestBed, inject } from '@angular/core/testing';

import { UploadTrxService } from './upload-trx.service';

describe('UploadTrxService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UploadTrxService]
    });
  });

  it('should be created', inject([UploadTrxService], (service: UploadTrxService) => {
    expect(service).toBeTruthy();
  }));
});
