import { TestBed, inject } from '@angular/core/testing';

import { ImportContactsService } from './import-contacts.service';

describe('ImportContactsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ImportContactsService]
    });
  });

  it('should be created', inject([ImportContactsService], (service: ImportContactsService) => {
    expect(service).toBeTruthy();
  }));
});
