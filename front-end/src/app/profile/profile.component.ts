import { Component, OnInit } from '@angular/core';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {

  constructor(private _formService: FormsService) { }

  ngOnInit() {
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }
    
  }

}
