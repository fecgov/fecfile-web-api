import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { CanActivateGuard } from '../shared/utils/can-activate/can-activate.guard';
import { CanDeactivateGuardService } from '../shared/services/CanDeactivateGuard/can-deactivate-guard.service';
import { ImportTransactionsComponent } from './import-transactions/import-transactions.component';



const routes: Routes = [
  {
    path: '',
    component: ImportTransactionsComponent,
    pathMatch: 'full',
    canActivate: [CanActivateGuard],
    canDeactivate: [CanDeactivateGuardService]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ImportTransactionsRoutingModule { }
