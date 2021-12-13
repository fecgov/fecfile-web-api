import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportTrxFileSelectComponent } from './import-trx-file-select.component';

describe('ImportTrxFileSelectComponent', () => {
  let component: ImportTrxFileSelectComponent;
  let fixture: ComponentFixture<ImportTrxFileSelectComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxFileSelectComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxFileSelectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
