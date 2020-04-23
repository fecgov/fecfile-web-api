import { TitleCasePipe } from '@angular/common';
import { F1mCandidatesTableComponent } from './../f1m-candidates-table/f1m-candidates-table/f1m-candidates-table.component';
import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared.module';
import { F1mPreviewComponent } from '../f1m-preview/f1m-preview/f1m-preview.component';
import { F1mQualificationComponent } from '../f1m-qualification/f1m-qualification/f1m-qualification.component';
import { F1mTypeComponent } from '../f1m-type/f1m-type/f1m-type.component';
import { F1mAffiliationComponent } from './../f1m-affiliation/f1m-affiliation/f1m-affiliation.component';
import { F1mRoutingModule } from './f1m-routing.module';
import { F1mComponent } from './f1m.component';


@NgModule({
  imports: [
    SharedModule,
    F1mRoutingModule,
  ],
  declarations: [
    F1mComponent,
    F1mTypeComponent,
    F1mAffiliationComponent,
    F1mPreviewComponent,
    F1mQualificationComponent,
    F1mCandidatesTableComponent
  ], 
  providers: [TitleCasePipe]
})
export class F1mModule { }
