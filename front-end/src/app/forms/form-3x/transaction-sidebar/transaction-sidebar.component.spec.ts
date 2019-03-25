import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TransactionSidebarComponent } from './transaction-sidebar.component';

describe('FormSidebarComponent', () => {
  let component: TransactionSidebarComponent;
  let fixture: ComponentFixture<TransactionSidebarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TransactionSidebarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TransactionSidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
