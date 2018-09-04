import { Location } from '@angular/common';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Router, Routes } from '@angular/router';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { routes, AppRoutingModule } from './app-routing.module';
import { AppComponent } from '../app.component';
import { LoginComponent } from '../login/login.component';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { ProfileComponent } from '../profile/profile.component';

describe('AppRoutingModule', () => {
  let appRoutingModule: AppRoutingModule;
  let location: Location;
  let router: Router;
  let fixture;

  beforeEach(() => {
    appRoutingModule = new AppRoutingModule();

    TestBed.configureTestingModule({
      imports: [
        FormsModule,
        ReactiveFormsModule,
        RouterTestingModule.withRoutes(routes)
      ],
      declarations: [
        AppComponent,
        LoginComponent,
        DashboardComponent,
        ProfileComponent
      ],
      providers: [
        FormBuilder
      ]
    });

    router = TestBed.get(Router);
    location = TestBed.get(Location);

    fixture = TestBed.createComponent(AppComponent);
    router.initialNavigation();
  });

  it('should create an instance', () => {
    expect(appRoutingModule).toBeTruthy();
  });

  it('navigate to "" redirects you to login', fakeAsync(() => {
    router.navigate(['']);
    tick();
    expect(location.path()).toBe('');
  }));
});
