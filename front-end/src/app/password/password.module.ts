import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserInfoComponent } from './user-info/user-info.component';
import { PasswordRoutingModule } from './password.routing.module';
import {ReactiveFormsModule} from '@angular/forms';
import { ResetSelectorComponent } from './reset-selector/reset-selector.component';
import {SharedModule} from '../shared/shared.module';

@NgModule({
  imports: [
    SharedModule,
    CommonModule,
    PasswordRoutingModule,
    ReactiveFormsModule
  ],
  declarations: [UserInfoComponent, ResetSelectorComponent ],
})
export class PasswordModule { }
