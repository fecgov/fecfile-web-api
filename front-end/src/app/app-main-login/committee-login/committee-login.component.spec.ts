import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CommitteeLoginComponent } from './committee-login.component';

describe('CommitteeLoginComponent', () => {
  let component: CommitteeLoginComponent;
  let fixture: ComponentFixture<CommitteeLoginComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CommitteeLoginComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CommitteeLoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
