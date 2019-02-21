import { Component, OnInit } from '@angular/core';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-users',
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.scss']
})
export class UsersComponent implements OnInit {

  constructor( private _formService: FormsService) { }

  ngOnInit() {
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }
  }

}
