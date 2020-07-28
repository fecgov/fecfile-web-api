import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {LoginComponent} from './login/login.component';
import {BrowserModule} from '@angular/platform-browser';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {RouterModule} from '@angular/router';
import { TwoFactorLoginComponent } from './two-factor-login/two-factor-login.component';
import { ConfirmTwoFactorComponent } from './confirm-two-factor/confirm-two-factor.component';

@NgModule({
  imports: [
    CommonModule,
    BrowserModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule
  ],
  declarations: [LoginComponent, TwoFactorLoginComponent, ConfirmTwoFactorComponent],
  exports: [
      LoginComponent, TwoFactorLoginComponent
  ],
  entryComponents: [LoginComponent]
})
export class AppMainLoginModule { }
