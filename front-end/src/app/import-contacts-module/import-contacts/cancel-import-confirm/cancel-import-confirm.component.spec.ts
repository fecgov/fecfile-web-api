import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CancelImportConfirmComponent } from './cancel-import-confirm.component';

describe('CancelImportConfirmComponent', () => {
  let component: CancelImportConfirmComponent;
  let fixture: ComponentFixture<CancelImportConfirmComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CancelImportConfirmComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CancelImportConfirmComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
