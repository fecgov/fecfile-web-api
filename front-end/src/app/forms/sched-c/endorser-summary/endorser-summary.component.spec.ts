import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { EndorserSummaryComponent } from './endorser-summary.component';

describe('EndorserSummaryComponent', () => {
  let component: EndorserSummaryComponent;
  let fixture: ComponentFixture<EndorserSummaryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ EndorserSummaryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EndorserSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
