import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { TransactionsFilterSidbarComponent } from './transactions-filter-sidebar.component';



describe('TransactionsFilterSidbarComponent', () => {
  let component: TransactionsFilterSidbarComponent;
  let fixture: ComponentFixture<TransactionsFilterSidbarComponent>;

  beforeEach(async(() => {
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
