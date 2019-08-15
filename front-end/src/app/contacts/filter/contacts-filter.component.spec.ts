import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ContactsFilterComponent } from './contacts-filter.component';



describe('ContactsFilterSidbarComponent', () => {
  let component: ContactsFilterComponent;
  let fixture: ComponentFixture<ContactsFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContactsFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContactsFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
