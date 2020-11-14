import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTrxDoneComponent } from './import-trx-done.component';

describe('ImportTrxDoneComponent', () => {
  let component: ImportTrxDoneComponent;
  let fixture: ComponentFixture<ImportTrxDoneComponent>;

  beforeEach(async(() => {
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
