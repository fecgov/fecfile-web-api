import { TestBed, inject } from '@angular/core/testing';

import { InputDialogService } from './input-dialog.service';

describe('InputDialogService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [InputDialogService]
    });
  });

  it('should be created', inject([InputDialogService], (service: InputDialogService) => {
    expect(service).toBeTruthy();
  }));
});
