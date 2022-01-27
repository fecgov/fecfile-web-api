import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { DuplicateContactsComponent } from './duplicate-contacts.component';

describe('DuplicateContactsComponent', () => {
  let component: DuplicateContactsComponent;
  let fixture: ComponentFixture<DuplicateContactsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DuplicateContactsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DuplicateContactsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
