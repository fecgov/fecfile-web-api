import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportTrxStartComponent } from './import-trx-start.component';

describe('ImportTrxStartComponent', () => {
  let component: ImportTrxStartComponent;
  let fixture: ComponentFixture<ImportTrxStartComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxStartComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxStartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
