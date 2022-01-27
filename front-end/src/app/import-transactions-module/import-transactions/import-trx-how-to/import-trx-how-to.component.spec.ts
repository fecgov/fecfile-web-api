import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportTrxHowToComponent } from './import-trx-how-to.component';

describe('ImportTrxHowToComponent', () => {
  let component: ImportTrxHowToComponent;
  let fixture: ComponentFixture<ImportTrxHowToComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxHowToComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxHowToComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
