import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FormEntryComponent } from './form-entry.component';

describe('FormEntryComponent', () => {
  let component: FormEntryComponent;
  let fixture: ComponentFixture<FormEntryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FormEntryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FormEntryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
