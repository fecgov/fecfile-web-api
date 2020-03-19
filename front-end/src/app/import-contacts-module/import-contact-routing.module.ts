import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ImportContactsComponent } from './import-contacts/import-contacts.component';
import { FooComponent } from './foo/foo.component';
import { CanActivateGuard } from '../shared/utils/can-activate/can-activate.guard';
import { CanDeactivateGuardService } from '../shared/services/CanDeactivateGuard/can-deactivate-guard.service';



const routes: Routes = [
  {
    path: '',
    // component: FooComponent
    component: ImportContactsComponent,
    pathMatch: 'full',
    canActivate: [CanActivateGuard],
    canDeactivate: [CanDeactivateGuardService]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ImportContactsRoutingModule { }
