import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { InputModalComponent } from './input-modal.component';

describe('InputModalComponent', () => {
  let component: InputModalComponent;
  let fixture: ComponentFixture<InputModalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ InputModalComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(InputModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
