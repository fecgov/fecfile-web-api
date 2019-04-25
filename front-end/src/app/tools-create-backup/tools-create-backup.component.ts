import { Component, OnInit } from '@angular/core';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-tools-create-backup',
  templateUrl: './tools-create-backup.component.html',
  styleUrls: ['./tools-create-backup.component.scss']
})
export class ToolsCreateBackupComponent implements OnInit {

  constructor(      private _formService: FormsService) { }

  ngOnInit() {

    this._formService.clearDashBoardReportFilterOptions();
    
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }
   }

}
