import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ContactsFilterSidbarComponent } from './contacts-filter-sidebar.component';



describe('ContactsFilterSidbarComponent', () => {
  let component: ContactsFilterSidbarComponent;
  let fixture: ComponentFixture<ContactsFilterSidbarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContactsFilterSidbarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContactsFilterSidbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
