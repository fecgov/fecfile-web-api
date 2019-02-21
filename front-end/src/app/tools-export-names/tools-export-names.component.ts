import { Component, OnInit } from '@angular/core';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-tools-export-names',
  templateUrl: './tools-export-names.component.html',
  styleUrls: ['./tools-export-names.component.scss']
})
export class ToolsExportNamesComponent implements OnInit {

  constructor(private _formService: FormsService) { }

  ngOnInit() {
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }
  }

}
