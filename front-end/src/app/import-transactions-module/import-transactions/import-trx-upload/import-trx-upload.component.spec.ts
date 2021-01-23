import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTrxUploadComponent } from './import-trx-upload.component';

describe('ImportTrxUploadComponent', () => {
  let component: ImportTrxUploadComponent;
  let fixture: ComponentFixture<ImportTrxUploadComponent>;

  beforeEach(async(() => {
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
