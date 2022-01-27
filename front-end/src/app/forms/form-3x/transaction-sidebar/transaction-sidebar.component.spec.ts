import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { TransactionSidebarComponent } from './transaction-sidebar.component';

describe('FormSidebarComponent', () => {
  let component: TransactionSidebarComponent;
  let fixture: ComponentFixture<TransactionSidebarComponent>;

  beforeEach(waitForAsync(() => {
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
