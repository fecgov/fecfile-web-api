import { TestBed, inject } from '@angular/core/testing';

import { UploadContactsService } from './upload-contacts.service';

describe('UploadContactsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UploadContactsService]
    });
  });

  it('should be created', inject([UploadContactsService], (service: UploadContactsService) => {
    expect(service).toBeTruthy();
  }));
});
