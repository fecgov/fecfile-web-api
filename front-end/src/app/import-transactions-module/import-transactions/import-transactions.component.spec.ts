import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTransactionsComponent } from './import-transactions.component';

describe('ImportTransactionsComponent', () => {
  let component: ImportTransactionsComponent;
  let fixture: ComponentFixture<ImportTransactionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTransactionsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTransactionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
