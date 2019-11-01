import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { EndorserComponent } from '../endorser/endorser.component';

describe('IndividualReceiptComponent', () => {
  let component: EndorserComponent;
  let fixture: ComponentFixture<EndorserComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ EndorserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(EndorserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
