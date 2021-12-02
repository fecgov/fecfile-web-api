import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { CookieService } from 'ngx-cookie-service';
import { Observable, of } from 'rxjs';
import { DashboardComponent } from './dashboard.component';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { ApiService } from '../shared/services/APIService/api.service';

class MockApiService extends ApiService {
  public signIn(usr: string, pass: string): Observable<any> {
    const username: string = '1078935131';
    const password: string = 'test';

    if ((usr === username) && (pass === password)) {
      return of([{authenticated: true}]);
    }

    return of([{authenticated: false}]);
  }

  public getCommiteeDetails(): Observable<any> {
    return of({});
  }

  public fileForm99(): Observable<any> {
    return of({});
  }

  public getForm99(): Observable<any> {
    return of({});
  }
}

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
      ],
      declarations: [
        DashboardComponent,
        HeaderComponent,
        SidebarComponent
      ],
      providers: [
        CookieService
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
