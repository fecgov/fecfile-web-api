import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTrxCleanComponent } from './import-trx-clean.component';

describe('ImportTrxCleanComponent', () => {
  let component: ImportTrxCleanComponent;
  let fixture: ComponentFixture<ImportTrxCleanComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxCleanComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxCleanComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
