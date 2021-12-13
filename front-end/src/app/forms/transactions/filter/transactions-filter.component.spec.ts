import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { TransactionsFilterSidbarComponent } from './transactions-filter-sidebar.component';



describe('TransactionsFilterSidbarComponent', () => {
  let component: TransactionsFilterSidbarComponent;
  let fixture: ComponentFixture<TransactionsFilterSidbarComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ TransactionsFilterSidbarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TransactionsFilterSidbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
