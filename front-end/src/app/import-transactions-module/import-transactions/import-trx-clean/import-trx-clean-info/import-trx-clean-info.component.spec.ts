import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportTrxCleanInfoComponent } from './import-trx-clean-info.component';

describe('ImportTrxCleanInfoComponent', () => {
  let component: ImportTrxCleanInfoComponent;
  let fixture: ComponentFixture<ImportTrxCleanInfoComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxCleanInfoComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxCleanInfoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
