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
import { CanDeactivateGuardService } from './shared/services/CanDeactivateGuard/can-deactivate-guard.service';
import { DialogService } from './shared/services/DialogService/dialog.service';

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

import { ToolsImportTransactionsComponent } from './tools-import-transactions/tools-import-transactions.component';
import { ToolsImportNamesComponent } from './tools-import-names/tools-import-names.component';
import { ToolsExportNamesComponent } from './tools-export-names/tools-export-names.component';
import { ToolsMergeNamesComponent } from './tools-merge-names/tools-merge-names.component';
import { ToolsCreateBackupComponent } from './tools-create-backup/tools-create-backup.component';

import { AppConfigService } from './app-config.service';
import { ConfirmModalComponent } from './shared/partials/confirm-modal/confirm-modal.component';
import { FormSidebarComponent } from './shared/partials/form-sidebar/form-sidebar.component';

import { F3xComponent } from './forms/form-3x/f3x/f3x.component';
import { TransactionTypeComponent } from './forms/form-3x/transaction-type/transaction-type.component';

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
    SettingsComponent,
    ToolsImportTransactionsComponent,
    ToolsImportNamesComponent,
    ToolsExportNamesComponent,
    ToolsMergeNamesComponent,
    ToolsCreateBackupComponent,
    ConfirmModalComponent,
    FormSidebarComponent,
    F3xComponent,
    TransactionTypeComponent
  ],
  entryComponents: [
    ConfirmModalComponent
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
    DialogService,
    CanDeactivateGuardService,
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
