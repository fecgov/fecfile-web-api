import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportTrxCleanComponent } from './import-trx-clean.component';

describe('ImportTrxCleanComponent', () => {
  let component: ImportTrxCleanComponent;
  let fixture: ComponentFixture<ImportTrxCleanComponent>;

  beforeEach(waitForAsync(() => {
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
