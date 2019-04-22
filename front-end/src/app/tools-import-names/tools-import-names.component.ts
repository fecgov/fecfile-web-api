import { Component, OnInit, ViewEncapsulation, EventEmitter, Output } from '@angular/core';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { SessionService } from '../shared/services/SessionService/session.service';
import { ApiService } from '../shared/services/APIService/api.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { FormsComponent } from '../forms/forms.component';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-tools-import-names',
  templateUrl: './tools-import-names.component.html',
  styleUrls: ['./tools-import-names.component.scss']
})
export class ToolsImportNamesComponent implements OnInit {
   
  constructor(
    private _sessionService: SessionService,
    private _apiService: ApiService,
    private _modalService: NgbModal,
    private _messageService: MessageService,
    private _formService: FormsService) { }

  ngOnInit() {

    this._formService.clearDashBoardReportFilterOptions();
    
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
       this._formService.removeFormDashBoard("3X");
    }
  }

  
}
