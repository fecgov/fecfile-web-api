import { PasswordStrengthMeterModule } from 'angular-password-strength-meter';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';
import { SharedModule } from './../shared/shared.module';
import { ConfirmTwoFactorComponent } from './confirm-two-factor/confirm-two-factor.component';
import { ConsentModalComponent } from './consent-modal/consent-modal.component';
import { LoginComponent } from './login/login.component';
import { RegisterComponent } from './register/register.component';
import { TwoFactorLoginComponent } from './two-factor-login/two-factor-login.component';
import { CreatePasswordComponent } from './create-password/create-password.component';
import { PersonalKeyComponent } from './personal-key/personal-key.component';

@NgModule({
  imports: [
    SharedModule,
    CommonModule,
    PasswordStrengthMeterModule,
    BrowserModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule
  ],
  declarations: [LoginComponent, TwoFactorLoginComponent, ConfirmTwoFactorComponent, ConsentModalComponent, RegisterComponent, CreatePasswordComponent, PersonalKeyComponent],
  exports: [
      LoginComponent, TwoFactorLoginComponent, RegisterComponent
  ],
  entryComponents: [LoginComponent, ConsentModalComponent]
})
export class AppMainLoginModule { }
