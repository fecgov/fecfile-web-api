import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgSelectModule } from '@ng-select/ng-select';
import { NgxPaginationModule } from 'ngx-pagination';
import { StepsComponent } from './partials/steps/steps.component';

@NgModule({
  imports: [
    CommonModule,
  ],
  declarations: [
    StepsComponent,
  ],
  exports: [
    CommonModule,
    NgbModule,
    NgSelectModule,
    FormsModule,
    ReactiveFormsModule,
    NgxPaginationModule,
    StepsComponent,
  ]
})
export class SharedModule { }
