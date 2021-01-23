import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTrxFileSelectComponent } from './import-trx-file-select.component';

describe('ImportTrxFileSelectComponent', () => {
  let component: ImportTrxFileSelectComponent;
  let fixture: ComponentFixture<ImportTrxFileSelectComponent>;

  beforeEach(async(() => {
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
