import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { Form3XReporttypesidebarComponent } from './Report-type-sidebar.component';

describe('FormSidebarComponent', () => {
  let component: Form3XReporttypesidebarComponent;
  let fixture: ComponentFixture<Form3XReporttypesidebarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ Form3XReporttypesidebarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(Form3XReporttypesidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
