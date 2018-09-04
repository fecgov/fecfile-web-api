import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Observable, of } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
import { LoginComponent } from './login.component';

class MockAuthService {
  private _authenticated: boolean = false;

  public isSignedIn(): boolean {
    return this._authenticated;
  }
}

class MockApiService {
  public signIn(): Observable<any> {
    return of([{
      "username": "Antonette",
      "password": "test"
    }]);
  }
}

describe('LoginComponent', () => {
  let component:  LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authService: MockAuthService;
  let apiService: MockApiService;
  let httpMock: HttpTestingController;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        FormsModule,
        ReactiveFormsModule,
        HttpClientTestingModule,
        RouterTestingModule
      ],
      declarations: [ LoginComponent ],
      providers: [
        MockAuthService,
        MockApiService,
        FormBuilder,
        CookieService
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    httpMock = TestBed.get(HttpTestingController);

    authService = TestBed.get(MockAuthService);
    apiService = TestBed.get(MockApiService);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('isSignedIn returns false when user is not authenticated', () => {
    expect(authService.isSignedIn()).toBeFalsy();
  });

  it('should not allow empty fields to be submitted', () => {
    const username = component.frm.controls['commiteeId'];
    const password = component.frm.controls['loginPassword'];

    username.setValue('');
    password.setValue('');

    component.frm.markAsDirty();
    component.frm.markAsTouched();

    fixture.debugElement.query(By.css('form')).triggerEventHandler('ngSubmit', null);
    expect(component.frm.valid).toBeFalsy();
  });

  it('should return error for invalid user or password', () => {
    const username = component.frm.controls['commiteeId'];
    const password = component.frm.controls['loginPassword'];

    username.setValue('testuser');
    password.setValue('testpassword');

    component.frm.markAsDirty();
    component.frm.markAsTouched();

    fixture.debugElement.query(By.css('form')).triggerEventHandler('ngSubmit', null);

    console.log(component.frm);
  });
});
