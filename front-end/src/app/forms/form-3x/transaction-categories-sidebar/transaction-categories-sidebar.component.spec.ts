import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FormSidebarComponent } from './form-sidebar.component';

describe('FormSidebarComponent', () => {
  let component: FormSidebarComponent;
  let fixture: ComponentFixture<FormSidebarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FormSidebarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FormSidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
