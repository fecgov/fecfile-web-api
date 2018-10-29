import { RouterModule, Routes } from '@angular/router';
import { ModuleWithProviders } from '@angular/core';
import { CanActivateGuard } from './shared/utils/can-activate/can-activate.guard';
import { LoginComponent } from './login/login.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { ProfileComponent } from './profile/profile.component';
import { ToolsComponent } from './tools/tools.component';
import { ReportsComponent } from './reports/reports.component';
import { ContributorsComponent } from './contributors/contributors.component';
import { FormsComponent } from './forms/forms.component';
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
		  { path: 'contributors', component: ContributorsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] },
		  {
        path: 'forms/form/:form_id', component: FormsComponent, pathMatch: 'full', canActivate: [CanActivateGuard],
        children: [
          { path: ':form_step', component: FormsComponent, pathMatch: 'full', canActivate: [CanActivateGuard] }
        ]
      }
		]
    },
    { path: '**', redirectTo: '' }
];

export const routing = RouterModule.forRoot(AppRoutes);
