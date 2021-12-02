import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { CleanContactsComponent } from './clean-contacts.component';

describe('CleanContactsComponent', () => {
  let component: CleanContactsComponent;
  let fixture: ComponentFixture<CleanContactsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CleanContactsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CleanContactsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
