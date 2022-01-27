import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportTrxUploadComponent } from './import-trx-upload.component';

describe('ImportTrxUploadComponent', () => {
  let component: ImportTrxUploadComponent;
  let fixture: ComponentFixture<ImportTrxUploadComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxUploadComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
