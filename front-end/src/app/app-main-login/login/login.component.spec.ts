import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Observable, of } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
import { ApiService } from '../../shared/services/APIService/api.service';
import { AuthService } from '../../shared/services/AuthService/auth.service';
import { LoginComponent } from './login.component';

class MockAuthService extends AuthService {
  private _authenticated: boolean = false;

  public isSignedIn(): boolean {
    return this._authenticated;
  }
}

class MockApiService extends ApiService {
  public signIn(usr: string, pass: string): Observable<any> {
    const username: string = '1078935131';
    const password: string = 'test';

    if ((usr === username) && (pass === password)) {
      return of([{authenticated: true}]);
    }

    return of([{authenticated: false}]);
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
        {
          provide: AuthService,
          useClass: MockAuthService
        },
        {
          provide: ApiService,
          useClass: MockApiService
        },
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

    authService = TestBed.get(AuthService);
    apiService = TestBed.get(ApiService);
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

  it('logging in with a invalid user returns false, but form is valid', () => {
    const userValue: string = '1073935132';
    const passwordValue: string = 'testpassword';

    const username = component.frm.controls['commiteeId'];
    const password = component.frm.controls['loginPassword'];

    username.setValue(userValue);
    password.setValue(passwordValue);

    component.frm.markAsDirty();
    component.frm.markAsTouched();

    fixture.debugElement.query(By.css('form')).triggerEventHandler('ngSubmit', null);

    apiService.signIn(userValue, passwordValue)
      .subscribe(res => {
        expect(res.authenticated).toBeFalsy();
      });

    expect(component.frm.valid).toBeTruthy();
  });

  it('logging in with a valid user logs you in', () => {
    const userValue: string = '1078935131';
    const passwordValue: string = 'test';

    const username = component.frm.controls['commiteeId'];
    const password = component.frm.controls['loginPassword'];

    username.setValue(userValue);
    password.setValue(passwordValue);

    component.frm.markAsDirty();
    component.frm.markAsTouched();

    fixture.debugElement.query(By.css('form')).triggerEventHandler('ngSubmit', null);

    apiService.signIn(userValue, passwordValue)
      .subscribe(res => {
        console.log('res: ', res);
        expect(res[0].authenticated).toBeTruthy();
      });

    expect(component.frm.valid).toBeTruthy();
  });
});
