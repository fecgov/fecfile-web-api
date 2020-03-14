import { Component, OnInit , ChangeDetectionStrategy } from '@angular/core';
import { FormsService } from '../shared/services/FormsService/forms.service';
@Component({
  selector: 'app-contributors',
  templateUrl: './contributors.component.html',
  styleUrls: ['./contributors.component.scss']
})
export class ContributorsComponent implements OnInit {

  constructor(private _formService: FormsService) { }

  ngOnInit() {

    this._formService.clearDashBoardReportFilterOptions();
    
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      //console.log("ContributorsComponent ngOnInit...")
      this._formService.removeFormDashBoard("3X");
    }
  }
}
