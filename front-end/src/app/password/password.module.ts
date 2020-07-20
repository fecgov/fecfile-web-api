import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserInfoComponent } from './user-info/user-info.component';
import { PasswordRoutingModule } from './password.routing.module';
import {ReactiveFormsModule} from '@angular/forms';
import { ResetSelectorComponent } from './reset-selector/reset-selector.component';
import { CreatePasswordComponent } from './create-password/create-password.component';
import {SharedModule} from '../shared/shared.module';
import { PasswordStrengthBarComponent } from './password-strength-bar/password-strength-bar.component';

@NgModule({
  imports: [
    SharedModule,
    CommonModule,
    PasswordRoutingModule,
    ReactiveFormsModule
  ],
  declarations: [UserInfoComponent, ResetSelectorComponent, CreatePasswordComponent, PasswordStrengthBarComponent],
  exports: [PasswordStrengthBarComponent]
})
export class PasswordModule { }
