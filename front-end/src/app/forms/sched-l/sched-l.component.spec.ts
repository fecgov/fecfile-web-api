import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SchedLComponent } from './sched-l.component';

describe('SchedLComponent', () => {
  let component: SchedLComponent;
  let fixture: ComponentFixture<SchedLComponent>;

  beforeEach(async(() => {
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
