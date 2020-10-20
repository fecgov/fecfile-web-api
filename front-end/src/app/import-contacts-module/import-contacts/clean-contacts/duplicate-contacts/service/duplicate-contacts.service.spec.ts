import { TestBed, inject } from '@angular/core/testing';

import { DuplicateContactsService } from './duplicate-contacts.service';

describe('DuplicateContactsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [DuplicateContactsService]
    });
  });

  it('should be created', inject([DuplicateContactsService], (service: DuplicateContactsService) => {
    expect(service).toBeTruthy();
  }));
});
