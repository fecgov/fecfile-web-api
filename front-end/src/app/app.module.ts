import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { APP_INITIALIZER, CUSTOM_ELEMENTS_SCHEMA, NgModule } from '@angular/core';
import { HttpModule } from '@angular/http';
import { BrowserModule } from '@angular/platform-browser';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { AngularEditorModule } from '@kolkov/angular-editor';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ArchwizardModule } from 'angular-archwizard';
import { AngularFileUploaderModule } from 'angular-file-uploader';
import { UserIdleModule } from 'angular-user-idle';
import { CollapseModule } from 'ngx-bootstrap/collapse';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { CookieService } from 'ngx-cookie-service';
import { NgxEditorModule } from 'ngx-editor';
import { NgPipesModule } from 'ngx-pipes';
import { AccountComponent } from './account/account.component';
import { AppConfigService } from './app-config.service';
import { AppLayoutComponent } from './app-layout/app-layout.component';
import { AppComponent } from './app.component';
import { routing } from './app.routes';
import { AddNewContactComponent } from './contacts/addnew/addnew_contacts.component';
import { ContactsTableComponent } from './contacts/contacts-table/contacts-table.component';
import { TrashConfirmComponent2 } from './contacts/contacts-table/trash-confirm/trash-confirm.component';
import { ContactsComponent } from './contacts/contacts.component';
import { ContactsFilterComponent } from './contacts/filter/contacts-filter.component';
import { ContactsFilterTypeComponent } from './contacts/filter/filter-type/contacts-filter-type.component';
import { ContributorsComponent } from './contributors/contributors.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { F24Component } from './forms/form-24/f24/f24.component';
import { F3xComponent } from './forms/form-3x/f3x/f3x.component';
import { FinancialSummaryComponent } from './forms/form-3x/financial-summary/financial-summary.component';
import { IndividualReceiptComponent } from './forms/form-3x/individual-receipt/individual-receipt.component';
import { ReportTypeSidebarComponent } from './forms/form-3x/report-type-sidebar/report-type-sidebar.component';
import { ReportTypeComponent } from './forms/form-3x/report-type/report-type.component';
import { SchedEComponent } from './forms/form-3x/sched-e/sched-e/sched-e.component';
import { SchedH1Component } from './forms/form-3x/sched-h1/sched-h1.component';
import { SchedH5Component_TOBEDELETED } from './forms/form-3x/sched-h5/sched-h5.component';
import { SchedH6Component_TOBEDELETED } from './forms/form-3x/sched-h6/sched-h6.component';
import { TransactionSidebarComponent } from './forms/form-3x/transaction-sidebar/transaction-sidebar.component';
import { TransactionTypeComponent } from './forms/form-3x/transaction-type/transaction-type.component';
import { F99Component } from './forms/form-99/f99/f99.component';
import { ReasonComponent } from './forms/form-99/reason/reason.component';
import { TypeComponent } from './forms/form-99/type/type.component';
import { FormsComponent } from './forms/forms.component';
import { EndorserSummaryComponent } from './forms/sched-c/endorser-summary/endorser-summary.component';
import { EndorserComponent } from './forms/sched-c/endorser/endorser.component';
import { LoanSummaryComponent } from './forms/sched-c/loan-summary/loan-summary.component';
import { TrashConfirmComponent3 } from './forms/sched-c/loan-summary/trash-confirm/trash-confirm.component';
import { LoanComponent } from './forms/sched-c/loan.component';
import { LoanpaymentComponent } from './forms/sched-c/loanpayment/loanpayment.component';
import { SchedC1Component } from './forms/sched-c1/sched-c1.component';
import { DebtSummaryComponent } from './forms/sched-d/debt-summary/debt-summary.component';
import { SchedFCoreComponent } from './forms/sched-f-core/sched-f-core.component';
import { SchedFComponent } from './forms/sched-f/sched-f.component';
import { SchedH1Component_TOBEDELETED } from './forms/sched-h1/sched-h1.component';
import { SchedH2Component } from './forms/sched-h2/sched-h2.component';
import { SchedH3Component } from './forms/sched-h3/sched-h3.component';
import { SchedH4Component } from './forms/sched-h4/sched-h4.component';
import { SchedH5Component } from './forms/sched-h5/sched-h5.component';
import { SchedH6Component } from './forms/sched-h6/sched-h6.component';
import { SchedLComponent } from './forms/sched-l/sched-l.component';
import { TransactionsFilterTypeComponent } from './forms/transactions/filter/filter-type/transactions-filter-type.component';
import { TransactionsFilterComponent } from './forms/transactions/filter/transactions-filter.component';
import { SubTransactionsTableComponent } from './forms/transactions/sub-transactions-table/sub-transactions-table.component';
import { TransactionsTableComponent } from './forms/transactions/transactions-table/transactions-table.component';
import { TrashConfirmComponent1 } from './forms/transactions/transactions-table/trash-confirm/trash-confirm.component';
import { TransactionsComponent } from './forms/transactions/transactions.component';
import { HelpComponent } from './help/help.component';
import { ProfileComponent } from './profile/profile.component';
import { ReportdetailsComponent } from './reports/reportdetails/reportdetails.component';
import { ReportheaderComponent } from './reports/reportheader/reportheader.component';
import { ReportsComponent } from './reports/reports.component';
import { ReportsFilterTypeComponent } from './reports/reportsidebar/filter-type/reports-filter-type.component';
import { ReportsidebarComponent } from './reports/reportsidebar/reportsidebar.component';
import { SettingsComponent } from './settings/settings.component';
import { ConfirmModalComponent } from './shared/partials/confirm-modal/confirm-modal.component';
import { HeaderComponent } from './shared/partials/header/header.component';
import { PreviewComponent } from './shared/partials/preview/preview.component';
import { SidebarComponent } from './shared/partials/sidebar/sidebar.component';
import { SignComponent } from './shared/partials/sign/sign.component';
import { SubmitComponent } from './shared/partials/submit/submit.component';
import { TypeaheadComponent } from './shared/partials/typeahead/typeahead.component';
import { ValidateComponent } from './shared/partials/validate/validate.component';
import { FilterPipe } from './shared/pipes/filter/filter.pipe';
import { OrderByPipe } from './shared/pipes/order-by/order-by.pipe';
import { SafeHTMLPipe } from './shared/pipes/safeHTML/safe-html.pipe';
import { ZipCodePipe } from './shared/pipes/zip-code/zip-code.pipe';
import { CanDeactivateGuardService } from './shared/services/CanDeactivateGuard/can-deactivate-guard.service';
import { DialogService } from './shared/services/DialogService/dialog.service';
import { TokenInterceptorService } from './shared/services/TokenInterceptorService/token-interceptor-service.service';
import { SharedModule } from './shared/shared.module';
import { CanActivateGuard } from './shared/utils/can-activate/can-activate.guard';
import { UtilService } from './shared/utils/util.service';
import { ToolsCreateBackupComponent } from './tools-create-backup/tools-create-backup.component';
import { ToolsExportNamesComponent } from './tools-export-names/tools-export-names.component';
import { ToolsImportNamesComponent } from './tools-import-names/tools-import-names.component';
import { ToolsImportTransactionsComponent } from './tools-import-transactions/tools-import-transactions.component';
import { ToolsMergeNamesComponent } from './tools-merge-names/tools-merge-names.component';
import { ToolsComponent } from './tools/tools.component';
import { UsersComponent } from './users/users.component';

// import * as AWS from 'aws-sdk';
import * as AWS from 'aws-sdk/global';
import * as S3 from 'aws-sdk/clients/s3';
import {AppMainLoginModule} from './app-main-login/app-main-login.module';
import {AdminModule} from './admin/admin.module';

const appInitializerFn = (appConfig: AppConfigService) => {
  return () => {
    return appConfig.loadAppConfig();
  };
};

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    ProfileComponent,
    HeaderComponent,
    SidebarComponent,
    FormsComponent,
    AppLayoutComponent,
    ReportsComponent,
    ContributorsComponent,
    ToolsComponent,
    TransactionsComponent,
    TransactionsTableComponent,
    TransactionsFilterComponent,
    TransactionsFilterTypeComponent,
    SubTransactionsTableComponent,
    TrashConfirmComponent1,
    TrashConfirmComponent2,
    TrashConfirmComponent3,
    F99Component,
    TypeComponent,
    ReasonComponent,
    PreviewComponent,
    ValidateComponent,
    SignComponent,
    TypeaheadComponent,
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
    TransactionSidebarComponent,
    F3xComponent,
    TransactionTypeComponent,
    ReportTypeComponent,
    ReportTypeSidebarComponent,
    FinancialSummaryComponent,
    ZipCodePipe,
    FilterPipe,
    IndividualReceiptComponent,
    ReportsidebarComponent,
    ReportheaderComponent,
    ReportdetailsComponent,
    SafeHTMLPipe,
    OrderByPipe,
    ReportsFilterTypeComponent,
    ContactsComponent,
    ContactsTableComponent,
    AddNewContactComponent,
    ContactsFilterComponent,
    SchedFComponent,
    SchedH1Component,
    SchedH2Component,
    LoanComponent,
    LoanSummaryComponent,
    EndorserComponent,
    SchedC1Component,
    SchedH3Component,
    SchedH5Component,
    LoanpaymentComponent,
    SchedH4Component,
    LoanpaymentComponent,
    EndorserSummaryComponent,
    SchedH6Component,
    DebtSummaryComponent,
    SchedLComponent,
    ContactsFilterTypeComponent,
    SchedH5Component_TOBEDELETED,
    SchedH6Component_TOBEDELETED,
    SchedH1Component_TOBEDELETED,
    SchedEComponent,
    SchedFCoreComponent,
    HelpComponent,
    F24Component,
  ],
  entryComponents: [ConfirmModalComponent, TrashConfirmComponent1, TrashConfirmComponent2, TrashConfirmComponent3],
  imports: [
    SharedModule,
    AdminModule,
    AppMainLoginModule,
    BrowserModule,
    // NgSelectModule,
    // FormsModule,
    // ReactiveFormsModule,
    HttpClientModule,
    HttpModule,
    NoopAnimationsModule,
    routing,
    AngularFileUploaderModule,
    ArchwizardModule,
    NgxEditorModule,
    TooltipModule.forRoot(),
    CollapseModule.forRoot(),
    AngularEditorModule,
    // ModalModule.forRoot(),
    // NgxPaginationModule,
    NgPipesModule,
    UserIdleModule.forRoot({ idle: 780, timeout: 120, ping: 500000 })
  ],
  providers: [
    CookieService,
    CanActivateGuard,
    DialogService,
    CanDeactivateGuardService,
    AppConfigService,
    NgbActiveModal,
    {
      provide: APP_INITIALIZER,
      useFactory: appInitializerFn,
      multi: true,
      deps: [AppConfigService]
    },
    DecimalPipe,
    DatePipe,
    UtilService,
    OrderByPipe,
    { provide: HTTP_INTERCEPTORS, useClass: TokenInterceptorService, multi: true }
  ],
  exports:[
    SubTransactionsTableComponent
  ],
  bootstrap: [AppComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class AppModule { }
