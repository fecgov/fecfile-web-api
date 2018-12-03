import { RouterModule, Routes } from '@angular/router';
import { ModuleWithProviders } from '@angular/core';
import { CanActivateGuard } from './shared/utils/can-activate/can-activate.guard';
import { CanDeactivateGuard } from './shared/utils/can-deactivate/can-deactivate.guard';
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
		  { path: 'reports', component: ReportsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
		  { path: 'account', component: AccountComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
		  { path: 'users', component: UsersComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
		  { path: 'settings', component: SettingsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
		  { path: 'contributors', component: ContributorsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
		  {
        path: 'forms/form/:form_id', component: FormsComponent, pathMatch: 'full', canActivate: [CanActivateGuard], canDeactivate: [CanDeactivateGuard],
        children: [
          { path: ':form_step', component: FormsComponent, pathMatch: 'full', canActivate: [CanActivateGuard], canDeactivate: [CanDeactivateGuard] }
        ]
      }
		]
    },
    { path: '**', redirectTo: '' }
];

export const routing = RouterModule.forRoot(AppRoutes);
