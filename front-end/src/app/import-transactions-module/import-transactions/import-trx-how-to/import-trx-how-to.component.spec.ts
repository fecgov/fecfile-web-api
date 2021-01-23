import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTrxHowToComponent } from './import-trx-how-to.component';

describe('ImportTrxHowToComponent', () => {
  let component: ImportTrxHowToComponent;
  let fixture: ComponentFixture<ImportTrxHowToComponent>;

  beforeEach(async(() => {
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
