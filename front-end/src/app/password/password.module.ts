import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserInfoComponent } from './user-info/user-info.component';
import { PasswordRoutingModule } from './password.routing.module';
import {ReactiveFormsModule} from '@angular/forms';

@NgModule({
  imports: [
    CommonModule,
    PasswordRoutingModule,
    ReactiveFormsModule
  ],
  declarations: [UserInfoComponent]
})
export class PasswordModule { }
