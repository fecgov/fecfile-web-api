import { RouterModule, Routes } from '@angular/router';
import { ModuleWithProviders } from '@angular/core';
import { CanActivateGuard } from './shared/utils/can-activate/can-activate.guard';
import { CanDeactivateGuardService } from './shared/services/CanDeactivateGuard/can-deactivate-guard.service';
import { LoginComponent } from './login/login.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { ProfileComponent } from './profile/profile.component';
import { ToolsComponent } from './tools/tools.component';
import { ReportsComponent } from './reports/reports.component';
import { ContributorsComponent } from './contributors/contributors.component';
import { FormsComponent } from './forms/forms.component';
import { AccountComponent } from './account/account.component';
import { UsersComponent } from './users/users.component';
import { SettingsComponent } from './settings/settings.component';
import { AppLayoutComponent } from './app-layout/app-layout.component';

import { ToolsImportTransactionsComponent } from './tools-import-transactions/tools-import-transactions.component';
import { ToolsImportNamesComponent } from './tools-import-names/tools-import-names.component';
import { ToolsExportNamesComponent } from './tools-export-names/tools-export-names.component';
import { ToolsMergeNamesComponent } from './tools-merge-names/tools-merge-names.component';
import { ToolsCreateBackupComponent } from './tools-create-backup/tools-create-backup.component';
import { TransactionsComponent } from './forms/transactions/transactions.component';
import { IndividualReceiptComponent } from './forms/form-3x/individual-receipt/individual-receipt.component';

import { ReportsidebarComponent } from './reports/reportsidebar/reportsidebar.component';
import { ReportheaderComponent } from './reports/reportheader/reportheader.component';
import { ReportdetailsComponent } from './reports/reportdetails/reportdetails.component';
import { SignComponent } from './shared/partials/sign/sign.component';
import { SubmitComponent } from './shared/partials/submit/submit.component';
import { ContactsComponent } from './contacts/contacts.component';
import { AddNewContactComponent } from './contacts/addnew/addnew_contacts.component';
import { HelpComponent } from './help/help.component';

export const AppRoutes: Routes = [
  {
    path: '',
    component: LoginComponent,
    pathMatch: 'full'
  },
  {
    path: '',
    component: AppLayoutComponent,
    children: [
      { path: 'dashboard', component: DashboardComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      { path: 'profile', component: ProfileComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      { path: 'tools', component: ToolsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      {
        path: 'reports',
        component: ReportheaderComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        children: [
          {
            path: 'reports/reportdetails',
            component: ReportdetailsComponent,
            pathMatch: 'full',
            canActivate: [CanActivateGuard],
            canDeactivate: [CanDeactivateGuardService]
          } /*  */
        ]
      },
      { path: 'account', component: AccountComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      {
        path: 'tools_import_transactions',
        component: ToolsImportTransactionsComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard]
      },
      {
        path: 'tools_import_names',
        component: ToolsImportNamesComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard]
      },
      {
        path: 'tools_export_names',
        component: ToolsExportNamesComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard]
      },
      {
        path: 'tools_merge_names',
        component: ToolsMergeNamesComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard]
      },
      {
        path: 'tools_create_backup',
        component: ToolsCreateBackupComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard]
      },
      { path: 'users', component: UsersComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      { path: 'settings', component: SettingsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      { path: 'contacts', component: ContactsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      {
        path: 'forms/form/:form_id',
        component: FormsComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService],
        // runGuardsAndResolvers: 'paramsOrQueryParamsChange',
        children: [
          {
            path: ':form_step',
            component: FormsComponent,
            pathMatch: 'full',
            canActivate: [CanActivateGuard],
            canDeactivate: [CanDeactivateGuardService]
          }
        ]
      },
      {
        path: 'signandSubmit/:form_id',
        component: SignComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService]
      },
      { path: 'submitform/:form_id', component: SubmitComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      {
        path: 'forms/form/edit/:form_id/:report_id',
        component: IndividualReceiptComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService]
      },
      {
        path: 'addContact',
        component: AddNewContactComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService]
      },
      { path: 'help', component: HelpComponent, pathMatch: 'full', canActivate: [CanActivateGuard] }
    ]
  },
  { path: '**', redirectTo: '' }
];

export const routing = RouterModule.forRoot(AppRoutes, {
  useHash: true,
  enableTracing: false,
  onSameUrlNavigation: 'reload'
});
