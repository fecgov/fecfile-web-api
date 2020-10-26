import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportHowToComponent } from './import-how-to.component';

describe('ImportHowToComponent', () => {
  let component: ImportHowToComponent;
  let fixture: ComponentFixture<ImportHowToComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportHowToComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportHowToComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
