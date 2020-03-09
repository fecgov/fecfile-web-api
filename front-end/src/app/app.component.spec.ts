import { Location } from '@angular/common';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CookieService } from 'ngx-cookie-service';
import { AppRoutes, routing } from './app.routes';
import { AppComponent } from './app.component';
import { LoginComponent } from './app-main-login/login/login.component';
import { AppLayoutComponent } from './app-layout/app-layout.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { SidebarComponent } from './shared/partials/sidebar/sidebar.component';
import { ProfileComponent } from './profile/profile.component';
import { ToolsComponent } from './tools/tools.component';
import { ReportsComponent } from './reports/reports.component';
import { ContributorsComponent } from './contributors/contributors.component';
import { FormsComponent } from './forms/forms.component';

describe('AppRoutingModule', () => {
  let location: Location;
  let router: Router;
  let fixture;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        RouterTestingModule.withRoutes(AppRoutes),
        FormsModule,
        ReactiveFormsModule,
        HttpClientTestingModule
      ],
      declarations: [
        AppComponent,
        LoginComponent,
        AppLayoutComponent,
        DashboardComponent,
        SidebarComponent,
        ProfileComponent,
        ToolsComponent,
        ReportsComponent,
        ContributorsComponent,
        FormsComponent
      ],
      providers: [CookieService],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ],
    })
    .compileComponents();

    router = TestBed.get(Router);
    location = TestBed.get(Location);

    fixture = TestBed.createComponent(AppComponent);
    router.initialNavigation();
  });

  it('should create an instance', fakeAsync(() => {
    router.navigate(['']);
    tick();
    expect(location.path()).toBe('');
  }));
});
