import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { F1mAffiliationComponent } from './f1m-affiliation.component';

describe('F1mAffiliationComponent', () => {
  let component: F1mAffiliationComponent;
  let fixture: ComponentFixture<F1mAffiliationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ F1mAffiliationComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F1mAffiliationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
