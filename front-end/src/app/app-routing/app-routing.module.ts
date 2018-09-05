import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { CanActivateGuard } from '../shared/utils/can-activate/can-activate.guard';
import { LoginComponent } from '../login/login.component';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { ProfileComponent } from '../profile/profile.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { HeaderComponent } from '../shared/partials/header/header.component';

export const routes: Routes = [
  {path: '', redirectTo: '/', pathMatch: 'full'},
  {path: '', component: LoginComponent},
  {path: 'dashboard', component: DashboardComponent, pathMatch: 'full', canActivate: [CanActivateGuard]},
  {path: 'profile', component: ProfileComponent, pathMatch: 'full', canActivate: [CanActivateGuard]}
];

@NgModule({
  schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
  imports: [
    CommonModule,
    RouterModule.forRoot(routes),
    SidebarComponent,
    HeaderComponent
  ],
  declarations: [
    LoginComponent,
    DashboardComponent,
    ProfileComponent,
    SidebarComponent,
    HeaderComponent
  ],
  exports: [ RouterModule ]
})
export class AppRoutingModule { }
