import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { F24LinkModalComponent } from './f24-link-modal.component';

describe('F24LinkModalComponent', () => {
  let component: F24LinkModalComponent;
  let fixture: ComponentFixture<F24LinkModalComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ F24LinkModalComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F24LinkModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
