import { Component, OnInit } from '@angular/core';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit {

  constructor(private _formService: FormsService) { }

  ngOnInit() {
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
       this._formService.removeFormDashBoard("3X");
    }  
  }

}
