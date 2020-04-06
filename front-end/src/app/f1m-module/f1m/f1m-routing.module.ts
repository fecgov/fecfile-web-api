import { FormsComponent } from './../../forms/forms.component';
import { F1mComponent } from './f1m.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { CanActivateGuard } from '../../shared/utils/can-activate/can-activate.guard';
import { CanDeactivateGuardService } from '../../shared/services/CanDeactivateGuard/can-deactivate-guard.service';

const routes: Routes = [
  {
    path: '',
    component: F1mComponent,
    pathMatch: 'full',
    canActivate: [CanActivateGuard],
    canDeactivate: [CanDeactivateGuardService]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class F1mRoutingModule { }
