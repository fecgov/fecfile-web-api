import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-import-trx-clean-info',
  templateUrl: './import-trx-clean-info.component.html',
  styleUrls: ['./import-trx-clean-info.component.scss']
})
export class ImportTrxCleanInfoComponent implements OnInit {

  public showAdditionalInfo: boolean;

  constructor() { }

  ngOnInit() {
    this.showAdditionalInfo = true;
  }

  public toggleAdditionalInfo() {
    this.showAdditionalInfo = !this.showAdditionalInfo;
  }

}
