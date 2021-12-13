import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportTrxDoneComponent } from './import-trx-done.component';

describe('ImportTrxDoneComponent', () => {
  let component: ImportTrxDoneComponent;
  let fixture: ComponentFixture<ImportTrxDoneComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxDoneComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxDoneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
