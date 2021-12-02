import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { F1mQualificationComponent } from './f1m-qualification.component';

describe('F1mQualificationComponent', () => {
  let component: F1mQualificationComponent;
  let fixture: ComponentFixture<F1mQualificationComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ F1mQualificationComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F1mQualificationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
