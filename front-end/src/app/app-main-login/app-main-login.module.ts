import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import {LoginComponent} from './login/login.component';
import {BrowserModule} from '@angular/platform-browser';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {RouterModule} from '@angular/router';
import {CommitteeLoginComponent} from './committee-login/committee-login.component';

@NgModule({
  imports: [
    CommonModule,
    BrowserModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule
  ],
  declarations: [LoginComponent, CommitteeLoginComponent],
  exports: [
      LoginComponent,
      CommitteeLoginComponent
  ],
  entryComponents: [LoginComponent, CommitteeLoginComponent]
})
export class AppMainLoginModule { }
