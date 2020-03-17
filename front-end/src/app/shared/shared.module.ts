import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpModule } from '@angular/http';
import { BrowserModule } from '@angular/platform-browser';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { AngularEditorModule } from '@kolkov/angular-editor';
import { NgSelectModule } from '@ng-select/ng-select';
import { ArchwizardModule } from 'angular-archwizard';
import { AngularFileUploaderModule } from 'angular-file-uploader';
import { ModalModule } from 'ngx-bootstrap';
import { CollapseModule } from 'ngx-bootstrap/collapse';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { CookieService } from 'ngx-cookie-service';
import { NgxEditorModule } from 'ngx-editor';
import { NgxPaginationModule } from 'ngx-pagination';
import { NgPipesModule } from 'ngx-pipes';
import { DecimalPipe, DatePipe } from '@angular/common';

import { UserIdleModule } from 'angular-user-idle';
import { StepsComponent } from './partials/steps/steps.component';

@NgModule({
  imports: [
    CommonModule,
  ],
  declarations: [
    StepsComponent
  ],
  exports: [
    CommonModule,
    NgbModule,
    StepsComponent,
    NgSelectModule,
    FormsModule,
    ReactiveFormsModule
  ]
})
export class SharedModule { }
