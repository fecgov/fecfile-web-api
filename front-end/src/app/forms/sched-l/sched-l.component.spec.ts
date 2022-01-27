import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SchedLComponent } from './sched-l.component';

describe('SchedLComponent', () => {
  let component: SchedLComponent;
  let fixture: ComponentFixture<SchedLComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedLComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedLComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
