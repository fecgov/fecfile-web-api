import { TestBed, inject } from '@angular/core/testing';

import { ManageUserService } from './manage-user.service';

describe('ManageUserService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ManageUserService]
    });
  });

  it('should be created', inject([ManageUserService], (service: ManageUserService) => {
    expect(service).toBeTruthy();
  }));
});
