import { PersonalKeyComponent } from './app-main-login/personal-key/personal-key.component';
import { CreatePasswordComponent } from './app-main-login/create-password/create-password.component';
import { RouterModule, Routes } from '@angular/router';
import { AccountComponent } from './account/account.component';
// import { ImportContactsComponent } from './contacts/import/import-contacts/import-contacts.component';
import { ManageUserComponent } from './admin/manage-user/manage-user.component';
import { AppLayoutComponent } from './app-layout/app-layout.component';
import { ConfirmTwoFactorComponent } from './app-main-login/confirm-two-factor/confirm-two-factor.component';
import { LoginComponent } from './app-main-login/login/login.component';
import { RegisterComponent } from './app-main-login/register/register.component';
import { TwoFactorLoginComponent } from './app-main-login/two-factor-login/two-factor-login.component';
import { AddNewContactComponent } from './contacts/addnew/addnew_contacts.component';
import { ContactsComponent } from './contacts/contacts.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { IndividualReceiptComponent } from './forms/form-3x/individual-receipt/individual-receipt.component';
import { FormsComponent } from './forms/forms.component';
import { HelpComponent } from './help/help.component';
import { ProfileComponent } from './profile/profile.component';
import { ReportdetailsComponent } from './reports/reportdetails/reportdetails.component';
import { ReportheaderComponent } from './reports/reportheader/reportheader.component';
import { SettingsComponent } from './settings/settings.component';
import { Roles } from './shared/enums/Roles';
import { SignAndSubmitComponent } from './shared/partials/sign-and-submit/sign-and-submit.component';
import { SubmitComponent } from './shared/partials/submit/submit.component';
import { CanDeactivateGuardService } from './shared/services/CanDeactivateGuard/can-deactivate-guard.service';
import { CanActivateGuard } from './shared/utils/can-activate/can-activate.guard';
import { ToolsCreateBackupComponent } from './tools-create-backup/tools-create-backup.component';
import { ToolsExportNamesComponent } from './tools-export-names/tools-export-names.component';
import { ToolsImportNamesComponent } from './tools-import-names/tools-import-names.component';
import { ToolsImportTransactionsComponent } from './tools-import-transactions/tools-import-transactions.component';
import { ToolsMergeNamesComponent } from './tools-merge-names/tools-merge-names.component';
import { ToolsComponent } from './tools/tools.component';
import { UsersComponent } from './users/users.component';


export const AppRoutes: Routes = [
  {
    path: '',
    component: LoginComponent,
    pathMatch: 'full',
  },
  { path: 'register', component: RegisterComponent, pathMatch: 'full' },
  { path: 'enterSecCode', component: ConfirmTwoFactorComponent, pathMatch: 'full' },
  { path: 'createPassword', component: CreatePasswordComponent, pathMatch: 'full' },
  { path: 'showPersonalKey', component: PersonalKeyComponent, pathMatch: 'full' },
  { path: 'twoFactLogin', component: TwoFactorLoginComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
  { path: 'confirm-2f', component: ConfirmTwoFactorComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
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
        canActivate: [CanActivateGuard],
        data: {
          role: [Roles.CommitteeAdmin, Roles.Admin, Roles.Editor]
        }
      },
      {
        path: 'tools_import_names',
        component: ToolsImportNamesComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        data: {
          role: [Roles.CommitteeAdmin, Roles.Admin, Roles.Editor]
        }
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
        canActivate: [CanActivateGuard],
        data: {
          role: [Roles.CommitteeAdmin, Roles.Admin, Roles.Editor]
        }
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
        path: 'forms/form/1M',
        loadChildren: 'src/app/f1m-module/f1m/f1m.module#F1mModule'
      },
      {
        path: 'import-contacts',
        loadChildren: 'src/app/import-contacts-module/import-contacts.module#ImportContactsModule',
        data: {
          role: [Roles.CommitteeAdmin, Roles.BackupCommitteeAdmin, Roles.Admin, Roles.Editor]
        }
      },
      {
        path: 'addContact',
        component: AddNewContactComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService],
        data: {
          role: [Roles.CommitteeAdmin, Roles.BackupCommitteeAdmin, Roles.Admin, Roles.Editor]
        }
      },
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
        component: SignAndSubmitComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService],
        data: {
          role: [Roles.CommitteeAdmin, Roles.BackupCommitteeAdmin, Roles.Admin]
        }
      },
      {
        path: 'submitform/:form_id', component: SubmitComponent, pathMatch: 'full', canActivate: [CanActivateGuard],
        data: {
          role: [Roles.CommitteeAdmin, Roles.BackupCommitteeAdmin, Roles.Admin]
        }
      },
      {
        path: 'forms/form/edit/:form_id/:report_id',
        component: IndividualReceiptComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService],
        data: {
          role: [Roles.CommitteeAdmin, Roles.BackupCommitteeAdmin, Roles.Admin]
        }
      },
      { path: 'help', component: HelpComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
      {
        path: 'manage_users',
        component: ManageUserComponent,
        pathMatch: 'full',
        canActivate: [CanActivateGuard],
        canDeactivate: [CanDeactivateGuardService],
        data: {
          role: [Roles.CommitteeAdmin, Roles.BackupCommitteeAdmin]
        }
      },
    ]
  },
  { path: '**', redirectTo: '' }
];

export const routing = RouterModule.forRoot(AppRoutes, {
  useHash: true,
  enableTracing: false,
  onSameUrlNavigation: 'reload'
});
