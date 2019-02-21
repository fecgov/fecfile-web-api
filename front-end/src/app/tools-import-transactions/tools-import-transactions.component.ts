import { Component, OnInit } from '@angular/core';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-tools-import-transactions',
  templateUrl: './tools-import-transactions.component.html',
  styleUrls: ['./tools-import-transactions.component.scss']
})
export class ToolsImportTransactionsComponent implements OnInit {

  constructor( private _formService: FormsService) { }

  ngOnInit() {
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }
  }

}
