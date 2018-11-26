import { BrowserModule } from '@angular/platform-browser';
import { APP_INITIALIZER, CUSTOM_ELEMENTS_SCHEMA, NgModule, ModuleWithProviders } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { NgxEditorModule } from 'ngx-editor';
import { AngularFileUploaderModule } from "angular-file-uploader";
import { CookieService } from 'ngx-cookie-service';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { CollapseModule } from 'ngx-bootstrap/collapse';
import { ArchwizardModule } from 'angular-archwizard';
import { QuillModule } from 'ngx-quill';
import { AngularEditorModule } from '@kolkov/angular-editor';
import { NgbModule } from "@ng-bootstrap/ng-bootstrap";

import { CanActivateGuard } from './shared/utils/can-activate/can-activate.guard';

// import { CanDeactivateGuardService } from './shared/services/CanDeactivateGuard/can-deactivate-guard.service';

import { routing } from './app.routes';
import { AppComponent } from './app.component';
import { LoginComponent } from './login/login.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { ProfileComponent } from './profile/profile.component';
import { HeaderComponent } from './shared/partials/header/header.component';
import { SidebarComponent } from './shared/partials/sidebar/sidebar.component';
import { FormsComponent } from './forms/forms.component';
import { AppLayoutComponent } from './app-layout/app-layout.component';
import { ReportsComponent } from './reports/reports.component';
import { ContributorsComponent } from './contributors/contributors.component';
import { ToolsComponent } from './tools/tools.component';
import { FormComponent } from './forms/form-99/form/form.component';
import { TypeComponent } from './forms/form-99/type/type.component';
import { ReasonComponent } from './forms/form-99/reason/reason.component';
import { StepsComponent } from './shared/partials/steps/steps.component';
import { PreviewComponent } from './shared/partials/preview/preview.component';
import { ValidateComponent } from './shared/partials/validate/validate.component';
import { SignComponent } from './shared/partials/sign/sign.component';
import { SubmitComponent } from './shared/partials/submit/submit.component';
import { AccountComponent } from './account/account.component';
import { UsersComponent } from './users/users.component';
import { SettingsComponent } from './settings/settings.component';

import { AppConfigService } from './app-config.service';

 const appInitializerFn = (appConfig: AppConfigService) => {
  return () => {
    return appConfig.loadAppConfig();
  };
};

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    DashboardComponent,
    ProfileComponent,
    HeaderComponent,
    SidebarComponent,
    FormsComponent,
    AppLayoutComponent,
    ReportsComponent,
    ContributorsComponent,
    ToolsComponent,
    FormComponent,
    TypeComponent,
    ReasonComponent,
    StepsComponent,
    PreviewComponent,
    ValidateComponent,
    SignComponent,
    SubmitComponent,
    AccountComponent,
    UsersComponent,
    SettingsComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    HttpModule,
    routing,
    AngularFileUploaderModule,
    ArchwizardModule,
    NgxEditorModule,
    TooltipModule.forRoot(),
    CollapseModule.forRoot(),
    QuillModule,
    AngularEditorModule,
    NgbModule.forRoot()
  ],
  providers: [
    CookieService, 
    CanActivateGuard,
    AppConfigService,
    {
      provide: APP_INITIALIZER,
      useFactory: appInitializerFn,
      multi: true,
      deps: [AppConfigService]
    }    
  ],
  bootstrap: [AppComponent],
  schemas: [
    CUSTOM_ELEMENTS_SCHEMA
  ]
})
export class AppModule { }
