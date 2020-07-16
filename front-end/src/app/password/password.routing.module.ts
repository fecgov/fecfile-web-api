import {RouterModule, Routes} from '@angular/router';

import {NgModule} from '@angular/core';
import {UserInfoComponent} from './user-info/user-info.component';


const routes: Routes = [
    {
        path: 'reset-password',
        component: UserInfoComponent,
        pathMatch: 'full',
    }
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class PasswordRoutingModule {}
