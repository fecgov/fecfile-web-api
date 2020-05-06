import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ManageUserComponent } from './manage-user/manage-user.component';
import {ReactiveFormsModule} from '@angular/forms';
import {SortableColumnComponent} from './manage-user/sortable-column/sortable-column.componenet';
import {SortableTableDirective} from './manage-user/sortable-table/sortable-table.directive';

@NgModule({
  imports: [
    CommonModule,
    ReactiveFormsModule
  ],
  declarations: [ManageUserComponent, SortableColumnComponent, SortableTableDirective],
  exports: [ManageUserComponent, ]
})
export class AdminModule { }
