import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { F1mCandidatesTableComponent } from './f1m-candidates-table.component';

describe('F1mCandidatesTableComponent', () => {
  let component: F1mCandidatesTableComponent;
  let fixture: ComponentFixture<F1mCandidatesTableComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ F1mCandidatesTableComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F1mCandidatesTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
